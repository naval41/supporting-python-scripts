"""
Script to update interview dates for random records per company.
For each company, selects a random number (5-10) of interview records and updates their dates
to today-1, today-2, today-3, etc. (sequential dates going back).
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from datetime import datetime, timedelta
import random
from db_config import DB_CONFIG


def get_db_connection():
    """
    Create and return a PostgreSQL database connection.
    Sets the search_path to the configured schema.
    
    Returns:
        psycopg2.connection: Database connection object
    """
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        
        # Set the schema (search_path) - using safe identifier quoting
        schema = DB_CONFIG.get('schema', 'public')
        with conn.cursor() as cursor:
            # Use sql.Identifier to safely quote the schema name
            query = sql.SQL('SET search_path TO {}').format(
                sql.Identifier(schema)
            )
            cursor.execute(query)
        conn.commit()
        
        print(f"Connected to database '{DB_CONFIG['database']}' with schema '{schema}'")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise


def get_all_companies(cursor):
    """
    Get all distinct company IDs from the Interview table.
    
    Args:
        cursor: Database cursor
        
    Returns:
        list: List of company IDs
    """
    try:
        cursor.execute('SELECT DISTINCT "companyId" FROM "Interview"')
        companies = [row['companyId'] for row in cursor.fetchall()]
        return companies
    except psycopg2.Error as e:
        print(f"Error fetching companies: {e}")
        return []


def get_random_interviews_for_company(cursor, company_id, limit=5):
    """
    Get random interview records for a given company.
    
    Args:
        cursor: Database cursor
        company_id: Company ID to filter interviews
        limit: Number of random records to select (default: 5)
        
    Returns:
        list: List of interview IDs
    """
    try:
        # Use ORDER BY RANDOM() to get random records
        query = '''
            SELECT id 
            FROM "Interview" 
            WHERE "companyId" = %s 
            ORDER BY RANDOM() 
            LIMIT %s
        '''
        cursor.execute(query, (company_id, limit))
        interviews = [row['id'] for row in cursor.fetchall()]
        return interviews
    except psycopg2.Error as e:
        print(f"Error fetching interviews for company {company_id}: {e}")
        return []


def update_interview_dates(cursor, interview_ids, base_date):
    """
    Update interview dates for given interview IDs.
    Dates are set as base_date-1, base_date-2, base_date-3, etc. (sequential dates going back).
    
    Args:
        cursor: Database cursor
        interview_ids: List of interview IDs to update
        base_date: Base date (typically today)
    """
    try:
        for index, interview_id in enumerate(interview_ids, start=1):
            # Calculate date: today - index (1, 2, 3, 4, 5)
            new_date = base_date - timedelta(days=index)
            
            # Update the interview date
            update_query = '''
                UPDATE "Interview" 
                SET "date" = %s, "updatedAt" = %s
                WHERE id = %s
            '''
            current_timestamp = datetime.now()
            cursor.execute(update_query, (new_date, current_timestamp, interview_id))
            
            print(f"  Updated interview {interview_id}: date = {new_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
    except psycopg2.Error as e:
        print(f"Error updating interview dates: {e}")
        return False


def main():
    """
    Main function to update interview dates for all companies.
    """
    print("Starting interview date update process...")
    print("=" * 60)
    
    # Get base date (today)
    base_date = datetime.now()
    print(f"Base date: {base_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    conn = None
    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("Connected successfully!")
        print()
        
        # Get all companies
        print("Fetching all companies...")
        companies = get_all_companies(cursor)
        print(f"Found {len(companies)} companies")
        print()
        
        if not companies:
            print("No companies found. Exiting.")
            return
        
        # Process each company
        total_updated = 0
        for company_id in companies:
            print(f"Processing company: {company_id}")
            
            # Get random number of interviews (between 5 and 10) for this company
            random_limit = random.randint(5, 10)
            print(f"  Random limit selected: {random_limit}")
            interview_ids = get_random_interviews_for_company(cursor, company_id, limit=random_limit)
            
            if not interview_ids:
                print(f"  No interviews found for company {company_id}")
                print()
                continue
            
            print(f"  Found {len(interview_ids)} interview(s) to update")
            
            # Update dates for these interviews
            if update_interview_dates(cursor, interview_ids, base_date):
                total_updated += len(interview_ids)
                print(f"  Successfully updated {len(interview_ids)} interview(s)")
            else:
                print(f"  Failed to update interviews for company {company_id}")
            
            print()
        
        # Commit all changes
        print("Committing changes to database...")
        conn.commit()
        print(f"Successfully committed all changes!")
        print()
        print("=" * 60)
        print(f"Summary:")
        print(f"  Total companies processed: {len(companies)}")
        print(f"  Total interviews updated: {total_updated}")
        print("=" * 60)
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
            print("Rolled back all changes due to error.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        if conn:
            conn.rollback()
            print("Rolled back all changes due to error.")
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()

