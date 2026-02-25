"""
Intent Extraction Agent - converts natural language to structured IntentState.
Uses Google Gemini LLM to parse user queries into tables, columns, joins, filters, etc.
"""
import json
from typing import Any, Dict, List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ValidationError

from config import GEMINI_API_KEY
from src.logger import agent_logger

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0,
)


class Join(BaseModel):
    """Join definition between two tables."""

    table1: str
    table2: str
    column1: str
    column2: str


class Filter(BaseModel):
    """Filter condition with optional aggregation and subquery support."""

    column: str
    operator: str
    value: Optional[Any] = None
    aggregation: Optional[str] = None
    subquery: Optional["IntentState"] = None
    time_scope: Optional[str] = None


class Aggregation(BaseModel):
    """Aggregation (SUM, AVG, COUNT, etc.) on a column."""

    column: str
    function: str


class IntentState(BaseModel):
    """
    Structured representation of user intent for SQL generation.
    Produced by the Intent Agent from natural language input.
    """

    intent: str
    tables: List[str]
    columns: List[str]
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
      "time_scope" : "LAST_MONTH | LAST_WEEK | TODAY | YESTERDAY | THIS_YEAR | LAST_7_DAYS"

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
  "limit": 10,
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

TIME EXPRESSION RULES:

If the user refers to a relative date such as:
- last month
- last week
- yesterday
- today
- this year
- past 7 days

You MUST NOT compute actual dates.

Instead:
- Set operator to appropriate comparison (e.g., BETWEEN)
- Set value to null
- Set "time_scope" to one of:
    LAST_MONTH
    LAST_WEEK
    TODAY
    YESTERDAY
    THIS_YEAR
    LAST_7_DAYS

Do NOT generate literal dates.
Do NOT generate strings like "last month" in value.

Return ONLY JSON. No markdown. No explanations.
"""


class IntentAgent:
    """
    LLM-based Intent Extraction Agent.
    Converts natural language input into structured IntentState for SQL generation.
    """

    def __init__(self, model, schema_context: str):
        self.model = model
        self.schema_context = schema_context

    def run(self, query: str) -> IntentState:
        """Invoke LLM and parse response into IntentState."""
        try:
            completion = self.model.invoke(
                [
                    (
                        "system",
                        f"{INTENT_EXTRACTION_PROMPT}\n\n{self.schema_context}",
                    ),
                    ("human", query),
                ]
            )
            raw_output = completion.content
            parsed_json = self._extract_json(raw_output)
            intent_state = IntentState(**parsed_json)
            agent_logger.info("Intent extracted for query: %s", query[:50])
            return intent_state
        except ValidationError as e:
            agent_logger.error("IntentState validation failed: %s", e)
            raise ValueError(f"IntentState validation failed: {e}") from e
        except Exception as e:
            agent_logger.exception("IntentAgent error")
            raise RuntimeError(f"IntentAgent error: {e}") from e

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM output, handling markdown-wrapped responses."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
            raise ValueError("Failed to parse JSON from LLM output.") from None
