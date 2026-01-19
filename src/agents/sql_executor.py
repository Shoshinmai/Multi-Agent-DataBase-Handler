from sqlmodel import Session
from sqlalchemy import text


class SQLExecutorAgent:

    def __init__(self, engine):
        self.engine = engine

    def execute(self, sql: str):
        self._validate_sql(sql)

        with Session(self.engine) as session:
            result = session.exec(text(sql))
            rows = result.fetchall()
            columns = result.keys()

        return {
            "columns": list(columns),
            "rows": [list(row) for row in rows],
            "row_count": len(rows)
        }

    def _validate_sql(self, sql: str):
        normalized = sql.strip().lower()

        if not normalized.startswith("select"):
            raise ValueError("Only SELECT queries allowed.")

        if ";" in normalized[:-1]:
            raise ValueError("Multiple SQL statements detected.")

        blocked = ["drop", "truncate", "alter", "insert", "update", "delete"]
        for word in blocked:
            if word in normalized:
                raise ValueError(f"Blocked keyword: {word}")

# from src.database import engine

# executor = SQLExecutorAgent(engine)

# sql = """
# SELECT users.name, purchases.amount
# FROM users
# JOIN purchases ON users.id = purchases.user_id 
# ORDER BY purchases.amount DESC
# LIMIT 5;
# """
# # sql = """
# # SELECT *
# # FROM users;
# # """

# result = executor.execute(sql)

# print("Columns:", result["columns"])
# print("Rows:")
# for row in result["rows"]:
#     print(row)