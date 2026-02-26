"""
Deterministic SQL Generator - converts IntentState to valid SQL.
No LLM involved; produces predictable, safe SELECT queries.
"""
from typing import List

from src.agents.intent_agent import Filter, IntentState, Join
from src.logger import agent_logger


class SQLGeneratorAgent:
    """
    Converts validated IntentState into SQL query strings.
    Supports SELECT with joins, filters, aggregations, GROUP BY, ORDER BY, LIMIT.
    """

    def generate(self, state: IntentState) -> str:
        """Generate SQL from IntentState. Currently supports SELECT only."""
        intent = state.intent.upper()
        if intent == "SELECT":
            return self._generate_select(state)
        raise NotImplementedError(f"Intent '{intent}' not implemented yet.")

    def _generate_select(self, state: IntentState) -> str:
        """Build SELECT query from IntentState components."""
        query = []
        query.append(self._build_select_clause(state))
        query.append(f"FROM {state.tables[0]}")

        if state.joins:
            query.append(self._build_joins(state.joins))

        if state.filters:
            query.append(self._build_filters(state.filters))

        if state.group_by:
            query.append(f"GROUP BY {', '.join(state.group_by)}")

        if state.order_by:
            query.append(f"ORDER BY {', '.join(state.order_by)}")

        if state.limit is not None:
            query.append(f"LIMIT {state.limit}")

        sql = "\n".join(query) + ";"
        agent_logger.debug("Generated SQL: %s", sql[:100])
        return sql

    def _build_select_clause(self, state: IntentState) -> str:
        """Build SELECT clause: aggregations > columns > *."""
        if state.aggregations:
            agg_parts = [f"{agg.function}({agg.column})" for agg in state.aggregations]
            return "SELECT " + ", ".join(agg_parts)
        if state.columns:
            return "SELECT " + ", ".join(state.columns)
        return "SELECT *"

    def _build_joins(self, joins: List[Join]) -> str:
        """Build JOIN clauses from list of Join definitions."""
        join_clauses = []
        for j in joins:
            clause = (
                f"JOIN {j.table2} "
                f"ON {j.table1}.{j.column1} = {j.table2}.{j.column2}"
            )
            join_clauses.append(clause)
        return "\n".join(join_clauses)

    def _build_filters(self, filters: List[Filter]) -> str:
        """Build WHERE clause from filters (supports subqueries and aggregations)."""
        parts = []
        for f in filters:
            if f.subquery:
                subquery_sql = self.generate(f.subquery).rstrip(";")
                parts.append(f"{f.column} {f.operator} ({subquery_sql})")
            elif f.aggregation:
                parts.append(f"{f.aggregation}({f.column}) {f.operator} {f.value}")
            elif isinstance(f.value, tuple):
                start, end = f.value
                parts.append(f"{f.column} BETWEEN '{start}' AND '{end}'")
            else:
                parts.append(f"{f.column} {f.operator} {self._format_value(f.value)}")
        return "WHERE " + " AND ".join(parts)

    def _format_value(self, value) -> str:
        """Format filter value for SQL (quote strings, pass numbers as-is)."""
        if value is None:
            raise ValueError("Filter value is None and no subquery provided.")
        if isinstance(value, str):
            return f"'{value}'"
        return str(value)
