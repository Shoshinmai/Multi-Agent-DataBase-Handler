from typing import List
# from intent_agent import IntentState, Join, Filter, Aggregation
from src.agents.intent_agent import IntentState, Join, Filter, Aggregation
# from sqlgenerator import intent_state


class SQLGeneratorAgent:
    """
    Deterministic SQL Generator.
    Converts a validated IntentState → SQL Query string.
    """

    def generate(self, state: IntentState) -> str:
        intent = state.intent.upper()

        if intent == "SELECT":
            return self._generate_select(state)

        raise NotImplementedError(f"Intent '{intent}' not implemented yet.")

    def _generate_select(self, state: IntentState) -> str:
        query = []

        select_clause = self._build_select_clause(state)
        query.append(select_clause)

        from_clause = f"FROM {state.tables[0]}"
        query.append(from_clause)

        if state.joins:
            join_sql = self._build_joins(state.joins)
            query.append(join_sql)

        if state.filters:
            where_sql = self._build_filters(state.filters)
            query.append(where_sql)

        if state.group_by:
            group_sql = f"GROUP BY {', '.join(state.group_by)}"
            query.append(group_sql)

        if state.order_by:
            order_sql = f"ORDER BY {', '.join(state.order_by)}"
            query.append(order_sql)

        if state.limit is not None:
            limit_sql = f"LIMIT {state.limit}"
            query.append(limit_sql)

        return "\n".join(query) + ";"

    def _build_select_clause(self, state: IntentState) -> str:
        """
        SELECT fields builder.
        Priority:
            1. Aggregations
            2. Columns
            3. "*"
        """
        if state.aggregations:
            agg_parts = []
            for agg in state.aggregations:
                agg_parts.append(f"{agg.function}({agg.column})")
            return "SELECT " + ", ".join(agg_parts)

        if state.columns:
            return "SELECT " + ", ".join(state.columns)

        return "SELECT *"

    def _build_joins(self, joins: List[str]):
        """
        Build JOIN statements.
        """
        join_clause = []
        for i in joins:
            clause = (
                f"JOIN {i.table2} "
                f"ON {i.table1}.{i.column1} = {i.table2}.{i.column2}"
            )
        join_clause.append(clause)
        return "\n".join(join_clause)

    def _build_filters(self, filters: List[Filter]) -> str:
        """
        WHERE clause.
        """
        parts = []
        for f in filters:

            # CASE 1 — Subquery exists (DERIVED FILTER)
            if f.subquery:
                subquery_sql = self.generate(f.subquery).rstrip(";")
                parts.append(f"{f.column} {f.operator} ({subquery_sql})")

            # CASE 2 — Aggregated filter (HAVING handled separately if needed)
            elif f.aggregation:
                parts.append(f"{f.aggregation}({f.column}) {f.operator} {f.value}")

            # CASE 3 — Normal filter
            else:
                parts.append(f"{f.column} {f.operator} {self._format_value(f.value)}")

        return "WHERE " + " AND ".join(parts)

    def _format_value(self, value):
        if value is None:
            raise ValueError("Filter value is None and no subquery provided.")

        if isinstance(value, str):
            return f"'{value}'"

        return value

    # parts = []
    # for f in filters:
    #     value = (
    #         f"'{f.value}'"
    #         if isinstance(f.value, str) and not f.value.upper().startswith("DATE(")
    #         else f.value
    #     )
    #     parts.append(f"{f.column} {f.operator} {value}")

    # return "WHERE " + " AND ".join(parts)


# intent_state = IntentState(
#     intent="SELECT",
#     tables=["users", "purchases"],
#     columns=["users.id", "users.name"],
#     joins=[Join(table1="users", table2="purchases", column1="id", column2="user_id")],
#     filters=[
#         Filter(
#             column="purchases.amount",
#             operator=">",
#             value=None,
#             aggregation=None,
#             subquery=IntentState(
#                 intent="SELECT",
#                 tables=["purchases"],
#                 columns=[],
#                 joins=[],
#                 filters=[],
#                 group_by=[],
#                 order_by=[],
#                 aggregations=[Aggregation(column="amount", function="AVG")],
#                 limit=None,
#             ),
#         )
#     ],
#     group_by=[],
#     order_by=[],
#     aggregations=[],
#     limit=None,
# )
# intent_state = IntentState(
#     intent="SELECT",
#     tables=["sales", "users"],
#     columns=["users.name", "SUM(sales.amount)"],
#     joins=[
#         Join(
#             table1="sales", table2="users", column1="sales.user_id", column2="users.id"
#         )
#     ],
#     filters=[
#         Filter(column="sales.date", operator=">=", value="last_week_start_date"),
#         Filter(column="sales.date", operator="<=", value="last_week_end_date"),
#     ],
#     group_by=["users.name"],
#     order_by=[],
#     aggregations=[Aggregation(column="sales.amount", function="SUM")],
#     limit=None,
# )

# intent_state = IntentState(
#     intent="SELECT",
#     tables=["users"],
#     columns=["*"],
#     joins=[],
#     filters=[],
#     group_by=[],
#     order_by=[],
#     aggregations=[],
#     limit=None,
# )
# generator = SQLGeneratorAgent()
# sql = generator.generate(intent_state)
# print(sql)
