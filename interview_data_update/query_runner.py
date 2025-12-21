#!/usr/bin/env python3
"""
Database Query Runner
A simple script to execute SQL queries and display results in terminal
Just run the script and enter your query when prompted
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG
from typing import List, Dict, Any


class DatabaseQueryRunner:
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Set schema if specified
            if DB_CONFIG.get('schema') and DB_CONFIG['schema'] != 'public':
                self.cursor.execute(f"SET search_path TO {DB_CONFIG['schema']}, public;")
            
            print(f"✓ Connected to database: {DB_CONFIG['database']} on {DB_CONFIG['host']}")
            if DB_CONFIG.get('schema'):
                print(f"✓ Using schema: {DB_CONFIG['schema']}")
            print()
            
        except psycopg2.Error as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            self.cursor.execute(query)
            
            # Check if query returns results (SELECT, etc.)
            if self.cursor.description:
                results = self.cursor.fetchall()
                return [dict(row) for row in results]
            else:
                # For INSERT, UPDATE, DELETE, etc.
                affected_rows = self.cursor.rowcount
                self.connection.commit()
                return [{"message": f"Query executed successfully. Rows affected: {affected_rows}"}]
                
        except psycopg2.Error as e:
            self.connection.rollback()
            raise Exception(f"Query execution failed: {e}")
    
    def print_results(self, results: List[Dict[str, Any]]):
        """Print query results in a simple, readable format"""
        if not results:
            print("No results returned.")
            return
        
        # Handle non-SELECT queries
        if len(results) == 1 and "message" in results[0]:
            print(results[0]["message"])
            return
        
        # Get column names
        columns = list(results[0].keys())
        
        # Calculate column widths (with reasonable limits)
        col_widths = {}
        for col in columns:
            col_widths[col] = len(str(col))
            for row in results:
                value = str(row[col]) if row[col] is not None else 'NULL'
                # Limit individual column width to 50 characters for readability
                display_value = value[:47] + "..." if len(value) > 50 else value
                col_widths[col] = max(col_widths[col], len(display_value))
            # Cap column width at 50
            col_widths[col] = min(col_widths[col], 50)
        
        # Print header
        header = " | ".join(f"{col:<{col_widths[col]}}" for col in columns)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in results:
            row_values = []
            for col in columns:
                value = str(row[col]) if row[col] is not None else 'NULL'
                # Truncate long values
                if len(value) > 50:
                    value = value[:47] + "..."
                row_values.append(f"{value:<{col_widths[col]}}")
            print(" | ".join(row_values))
        
        print(f"\nTotal rows: {len(results)}")
    
    def get_query_from_user(self):
        """Get SQL query from user input"""
        print("Enter your SQL query:")
        print("(You can use multiple lines. Press Enter on an empty line when finished)")
        print("=" * 60)
        
        query_lines = []
        while True:
            try:
                line = input()
                # If user presses Enter on empty line, we're done
                if line.strip() == '':
                    break
                query_lines.append(line)
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None
            except EOFError:
                break
        
        query = '\n'.join(query_lines).strip()
        if not query:
            print("No query entered.")
            return None
        
        return query
    
    def run_interactive(self):
        """Run the query runner interactively"""
        print("=== Database Query Runner ===")
        print("Enter your SQL query below. No need to worry about escaping!")
        print()
        
        while True:
            query = self.get_query_from_user()
            
            if query is None:
                break
            
            print("\nExecuting query...")
            print("-" * 40)
            
            try:
                results = self.execute_query(query)
                self.print_results(results)
                
            except Exception as e:
                print(f"✗ Error: {e}")
            
            print("\n" + "=" * 60)
            
            # Ask if user wants to run another query
            try:
                another = input("\nRun another query? (y/n): ").strip().lower()
                if another not in ['y', 'yes']:
                    break
            except (KeyboardInterrupt, EOFError):
                break
        
        print("\nGoodbye!")
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


def main():
    """Main function"""
    db = DatabaseQueryRunner()
    
    try:
        db.run_interactive()
    finally:
        db.close()


if __name__ == '__main__':
    main()