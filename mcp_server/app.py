import os

from fastmcp import FastMCP
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

mcp = FastMCP("My Server")

# Database connection
DB_USER = os.environ.get("MYSQL_USER")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD")
DB_HOST = os.environ.get("MYSQL_HOST")
DB_NAME = os.environ.get("MYSQL_DATABASE")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@mcp.tool(
    name="execute_sql",
    description="Executes a raw SQL query on the database.",
)
def execute_sql(sql_query: str) -> str:
    """Execute a raw SQL query."""
    db = SessionLocal()
    try:
        result_proxy = db.execute(text(sql_query))
        if result_proxy.returns_rows:
            results = result_proxy.fetchall()
            column_names = result_proxy.keys()
            formatted_results = [dict(zip(column_names, row))
                                 for row in results]
            if not formatted_results:
                return "Query executed successfully, but returned no results."
            return f"Query executed successfully. Results:\n{formatted_results}"
        else:
            db.commit()
            return f"Query executed successfully. {result_proxy.rowcount} row(s) affected."
    except Exception as e:
        db.rollback()
        return f"Error executing query: {e}"
    finally:
        db.close()


@mcp.resource("resource://greeting")
def get_greeting() -> str:
    return "Hello from FastMCP Resource"


if __name__ == "__main__":
    host = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_SERVER_PORT", 6000))
    mcp.run(port=port, host=host, transport="streamable-http")
