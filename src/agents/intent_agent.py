import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Dict, Any

from pydantic import ValidationError
from typing import List, Optional

# gemini_key = os.getenv("gemini_api_key")
gemini_key = "AIzaSyCbKbhdIgYLC_ECAdoXK6SB7htSh6P83VU"
print(os.getenv("gemini_api_key"))

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", google_api_key=gemini_key, temperature=0
)


class Join(BaseModel):
    table1: str
    table2: str
    column1: str
    column2: str


class Filter(BaseModel):
    column: str
    operator: str
    value: str


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

Return ONLY a **valid JSON object**, nothing else. No explanations.

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
      "value": "string"
    }
  ],
  "group_by": ["col1", "col2"],
  "order_by": ["col1 DESC", "col2 ASC"],
  "aggregations": [
    {
      "column": "string",
      "function": "SUM | COUNT | AVG | MIN | MAX"
    }
  ],
  "limit": 10
}

If information is missing, return empty arrays or null values.
ALWAYS include the key even if the list is empty.

Return ONLY JSON. Use exactly these keys:

{
  "intent": "...",
  "tables": [...],
  "columns": [...],
  "joins": [...],
  "filters": [...],
  "aggregations": [...],
  "group_by": [...],
  "order_by": [...],
  "limit": ...
}

Do NOT include: query, reasoning, confidence, action, metadata, or any extra fields.
If the user asks "what is my query?", DO NOT add a 'query' field.
Always use "intent", NOT "action".
"""




class IntentAgent:
    """
    LLM-based Intent Extraction Agent.
    Converts natural language input→structured IntentState.
    """

    def __init__(self, model):
        """
        model = Gemini Model
        Example:
            model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")
        """
        self.model = model

    def run(self, query: str) -> IntentState:
        """
        Run the LLM and return a parsed IntentState object.
        """
        try:
            completion = self.model.invoke(
                [
                    (
                        "system",
                        f"{INTENT_EXTRACTION_PROMPT}",
                    ),
                    ("human", f"{query}"),
                ]
            )

            raw_output = completion.content
            # print(raw_output)

            # Force JSON extraction
            parsed_json = self._extract_json(raw_output)

            # Validate using Pydantic model
            print(IntentState(**parsed_json))
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


agent = IntentAgent(llm)
result = agent.run("show me total sales by each user last week")

# print(result)
