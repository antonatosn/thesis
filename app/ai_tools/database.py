"""This module provides a tool for executing raw SQL queries against the database."""
import traceback
from typing import Type

from crewai.tools import BaseTool
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pydantic import BaseModel, Field
from sqlalchemy import text


class UnsafeDatabaseQueryToolSchema(BaseModel):
    """Input schema for the UnsafeDatabaseQueryTool."""
    sql_query: str = Field(..., description="The raw SQL query to be executed against the database.")

class UnsafeDatabaseQueryTool(BaseTool):
    name: str = "Unsafe Database SQL Executor"
    description: str = (
        "Executes any raw SQL query you provide directly on the database. "
        "Use this to find, add, modify, or delete data from tables like 'users', 'cars', 'quotes', and 'insurance_products'. "
        "Input must be a valid SQL query string."
    )
    args_schema: Type[BaseModel] = UnsafeDatabaseQueryToolSchema
    db: SQLAlchemy | None = None
    app: Flask | None = None

    def __init__(self, db: SQLAlchemy, app: Flask, **kwargs):
        """
        Initializes the tool by injecting the Flask app and SQLAlchemy db instances.
        
        Args:
            db (SQLAlchemy): The Flask-SQLAlchemy instance from the main application.
            app (Flask): The Flask application instance.
        """
        super().__init__(**kwargs)
        if not isinstance(db, SQLAlchemy):
            raise TypeError("The 'db' parameter must be an instance of Flask-SQLAlchemy.")
        if not isinstance(app, Flask):
            raise TypeError("The 'app' parameter must be an instance of Flask.")
        
        self.db = db
        self.app = app

    def _run(self, sql_query: str) -> str:
        # Use the injected app and db instances
        with self.app.app_context():
            try:
                # Use the injected db session to execute the query
                result_proxy = self.db.session.execute(text(sql_query))
                
                if result_proxy.returns_rows:
                    results = result_proxy.fetchall()
                    column_names = result_proxy.keys()
                    formatted_results = [dict(zip(column_names, row)) for row in results]
                    
                    if not formatted_results:
                        return "Query executed successfully, but returned no results."
                    return f"Query executed successfully. Results:\n{formatted_results}"
                else:
                    self.db.session.commit()
                    return f"Query executed successfully. {result_proxy.rowcount} row(s) affected."

            except Exception as e:
                self.db.session.rollback()
                return f"Error executing query: {e}\n{traceback.format_exc()}"