"""
Database configuration constants for PostgreSQL connection.
Update these values with your actual database credentials.
"""

# PostgreSQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'roundz',
    'schema': 'prod_db_v4'  # Database schema name (default: 'public')
}

# Alternative: You can also use environment variables
# Uncomment and use if you prefer environment variables
# import os
# DB_CONFIG = {
#     'host': os.getenv('DB_HOST', 'localhost'),
#     'port': int(os.getenv('DB_PORT', 5432)),
#     'database': os.getenv('DB_NAME', 'your_database_name'),
#     'user': os.getenv('DB_USER', 'your_username'),
#     'password': os.getenv('DB_PASSWORD', 'your_password'),
#     'schema': os.getenv('DB_SCHEMA', 'public')
# }