from sqlmodel import Session
from sqlalchemy import text
# from src.database import engine


class SchemaExtractor:
    def __init__(self, engine):
        self.engine = engine

    def extract_schema(self) -> dict:
        """
        Returns structured schema info:
        {
            "users": {
                "columns": [
                    {"name": "id", "type": "integer"},
                    ...
                ]
            },
            ...
        }
        """

        schema = {}

        with Session(self.engine) as session:

            # Get tables
            tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """

            tables = session.exec(text(tables_query)).fetchall()

            for (table_name,) in tables:

                columns_query = """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = :table;
                """

                stmt = text(columns_query).bindparams(table=table_name)
                columns = session.exec(stmt).fetchall()

                schema[table_name] = {
                    "columns": [{"name": col[0], "type": col[1]} for col in columns]
                }

        return schema


def format_schema_for_prompt(schema: dict) -> str:
    formatted = "Database Schema:\n\n"

    for table, info in schema.items():
        formatted += f"Table: {table}\n"
        for column in info["columns"]:
            formatted += f"- {column['name']} ({column['type']})\n"
        formatted += "\n"
    print(formatted)
    return formatted

# extr = SchemaExtractor(engine)
# res = extr.extract_schema()
# form = format_schema_for_prompt(res)
# print(form)