import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from .config import Config

class DBHelper:
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config or Config.get_db_config()
        self.connection = None

    def connect(self):
        """Establish database connection"""
        if not self.db_config:
            raise ValueError("Database configuration is missing.")
            
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get('host'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database'),
                user=self.db_config.get('user'),
                password=self.db_config.get('password')
            )
            # Set schema if specified
            # Set schema if specified
            schema = self.db_config.get('schema')
            print(f"DEBUG: Checking schema configuration. Schema: '{schema}'")
            if schema:
                print(f"DEBUG: Setting search_path to '{schema}, public'")
                with self.connection.cursor() as cursor:
                     cursor.execute(f"SET search_path TO {schema}, public;")
                print("DEBUG: Schema set successfully")
            else:
                print("DEBUG: No schema specified in config, using default search_path")
            
            return self.connection
        except psycopg2.Error as e:
            print(f"Database connection failed: {e}")
            raise

    def get_cursor(self):
        if not self.connection or self.connection.closed:
            self.connect()
        return self.connection.cursor(cursor_factory=RealDictCursor)

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results for SELECT, or commit for others.
        """
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params)
            
            if cursor.description:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                self.connection.commit()
                return [{"affected_rows": cursor.rowcount}]
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"Query execution failed: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        if self.connection:
            self.connection.close()
