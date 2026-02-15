import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv

from pydantic import ValidationError
from typing import List, Optional

load_dotenv()
gemini_key = os.getenv("gemini_api_key")
# gemini_key = "AIzaSyCbKbhdIgYLC_ECAdoXK6SB7htSh6P83VU"
# print(os.getenv("gemini_api_key"))

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", google_api_key=gemini_key, temperature=0
)


class Join(BaseModel):
    table1: str
    table2: str
    column1: str
    column2: str


class Filter(BaseModel):
    column: str
    operator: str
    # value: Optional[str] | Optional["IntentState"]  = None
    value: Optional[Any] = None
    aggregation: Optional[str] = None
    subquery: Optional["IntentState"] = None


class Aggregation(BaseModel):
    column: str
    function: str


class IntentState(BaseModel):
    intent: str  # e.g. "SELECT"
    tables: List[str]  # ["Sales", "Customers"]
    columns: List[str]  # ["sale_amount", "customer_name"]
    joins: Optional[List[Join]] = []
    filters: Optional[List[Filter]] = []
    group_by: Optional[List[str]] = []
    order_by: Optional[List[str]] = []
    aggregations: Optional[List[Aggregation]] = []
    limit: Optional[int] = None


INTENT_EXTRACTION_PROMPT = """
You are an Intent Extraction Agent for converting natural language into a structured JSON representation
for SQL query planning.

Return ONLY a valid JSON object. No explanations, no markdown, no extra text.

The JSON MUST follow this schema exactly:

{
  "intent": "SELECT | INSERT | UPDATE | DELETE",
  "tables": ["table1", "table2"],
  "columns": ["col1", "col2"],

  "joins": [
    {
      "table1": "string",
      "table2": "string",
      "column1": "string",
      "column2": "string"
    }
  ],

  "filters": [
    {
      "column": "string",
      "operator": "string",

      "value": "Any | None",

      "subquery": {
        "intent": "SELECT",
        "tables": ["table"],
        "columns": [],
        "joins": [],
        "filters": [],
        "aggregations": [
          {
            "column": "string",
            "function": "SUM | COUNT | AVG | MIN | MAX"
          }
        ],
        "group_by": [],
        "order_by": [],
        "limit": None
      }
    }
  ],

  "aggregations": [
    {
      "column": "string",
      "function": "SUM | COUNT | AVG | MIN | MAX"
    }
  ],

  "group_by": ["col1", "col2"],
  "order_by": ["col1 DESC", "col2 ASC"],
  "limit": 10
}

IMPORTANT RULES:

1. ALWAYS return ALL top-level keys:
   intent, tables, columns, joins, filters, aggregations, group_by, order_by, limit

2. If a key has no values, return an empty list [] or None (for limit).

3. NEVER include extra keys such as:
   query, reasoning, confidence, explanation, metadata, action

4. ALWAYS use "intent", NEVER use "action".

5. For simple filters, use:
   {
     "column": "...",
     "operator": "...",
     "value": "...",
     "subquery": None
   }

6. If a filter compares against a derived value (average, total, max, min, count),
   represent it as a SUBQUERY:
   - Set "value" to None
   - Populate the "subquery" object fully
   - DO NOT write raw SQL inside "value"

7. Subqueries MUST follow the SAME schema as the parent query
   (intent, tables, joins, filters, aggregations, group_by, order_by, limit).

8. Do NOT generate raw SQL strings anywhere.

FILTER AGGREGATION RULES:

- If a filter compares an aggregated value (average, sum, count, min, max),
  you MUST set the "aggregation" field in the filter.

Examples:

1) "users whose average purchase is greater than X"
→
{
  "column": "purchases.amount",
  "aggregation": "AVG",
  "operator": ">",
  "value": "X",
  "subquery": None
}

2) "users whose total sales are greater than the average total sales"
→
{
  "column": "purchases.amount",
  "aggregation": "SUM",
  "operator": ">",
  "value": None,
  "subquery": { ... }
}

- If the filter is NOT aggregated, set "aggregation" to None.
- NEVER infer aggregation implicitly.

WHERE vs HAVING RULES:

1. If the filter compares a RAW column value, do NOT use aggregation.
   → aggregation = null
   → This filter belongs to WHERE.

2. If the filter compares an AGGREGATED value (AVG, SUM, COUNT, MIN, MAX),
   you MUST set:
   - "aggregation": "AVG | SUM | COUNT | MIN | MAX"
   - AND include appropriate "group_by".

3. NEVER place a filter with aggregation=null into HAVING.

4. If aggregation is provided, GROUP BY is REQUIRED.


Return ONLY JSON. No markdown. No explanations.
"""


class IntentAgent:
    """
    LLM-based Intent Extraction Agent.
    Converts natural language input→structured IntentState.
    """

    def __init__(self, model, schema_context: str):
        """
        model = Gemini Model
        Example:
            model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")
        """
        self.model = model
        self.schema_context = schema_context

    def run(self, query: str) -> IntentState:
        """
        Run the LLM and return a parsed IntentState object.
        """
        try:
            completion = self.model.invoke(
                [
                    (
                        "system",
                        f"{INTENT_EXTRACTION_PROMPT}\n\n{self.schema_context}",
                    ),
                    ("human", f"{query}"),
                ]
            )

            raw_output = completion.content
            # print(raw_output)

            # Force JSON extraction
            parsed_json = self._extract_json(raw_output)
            # ps = IntentState(**parsed_json).split()
            # parsed_json = "]".join(IntentState(**parsed_json))
            # Validate using Pydantic model
            print(parsed_json)
            # print(IntentState(**parsed_json))
            return IntentState(**parsed_json)

        except ValidationError as e:
            raise ValueError(f"IntentState validation failed: {e}")

        except Exception as e:
            raise RuntimeError(f"IntentAgent error: {e}")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from the model output safely.
        """
        try:
            # print(f"Json ----->  {json.loads(text)}")
            return json.loads(text)
        except json.JSONDecodeError:
            # Attempt to find JSON substring
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)

            raise ValueError("Failed to parse JSON from LLM output.")


# agent = IntentAgent(llm)
# result = agent.run("users whose purchase is greater than the average of last month.")
# result = agent.run("Show all users who made more than the average purchase amount.")

# print(result.model_dump_json(indent=2))
# print(result)

# graph/nodes/intent_node.py

# def intent_node(state: GraphState, intent_agent):
#     intent = intent_agent.run(state.user_query)
#     return state.model_copy(update={"intent": intent})
