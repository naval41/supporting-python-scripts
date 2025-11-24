# Interview Date Update Script

This script updates interview dates for random records in the Interview table. For each company, it selects a random number (5-10) of interview records and updates their dates to sequential dates going back from today (today-1, today-2, today-3, etc.).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database credentials:
   - Copy `db_config.py.example` to `db_config.py`:
     ```bash
     cp db_config.py.example db_config.py
     ```
   - Open `db_config.py` and update the `DB_CONFIG` dictionary with your PostgreSQL credentials:
     - `host`: Database host (default: 'localhost')
     - `port`: Database port (default: 5432)
     - `database`: Database name
     - `user`: Database username
     - `password`: Database password
     - `schema`: Database schema name (default: 'public')
   
   **Important:** Add `db_config.py` to your `.gitignore` file to avoid committing credentials:
   ```
   interview_data_update/db_config.py
   ```

## Usage

Run the script:
```bash
python update_interview_dates.py
```

## What it does

1. Connects to the PostgreSQL database using credentials from `db_config.py`
2. Fetches all distinct company IDs from the Interview table
3. For each company:
   - Selects a random number (5-10) of interview records
   - Updates their `date` field to sequential dates going back:
     - today - 1 day
     - today - 2 days
     - today - 3 days
     - ... (continues for the number of records selected)
   - Updates the `updatedAt` timestamp to the current time
4. Commits all changes to the database

## Notes

- The script uses transactions, so if an error occurs, all changes will be rolled back
- For each company, a random number between 5 and 10 is selected as the limit
- If a company has fewer interviews than the random limit, it will update all available interviews
- The script uses `ORDER BY RANDOM()` to select random records for each company
- All database operations are logged to the console

## Example Output

```
Starting interview date update process...
============================================================
Base date: 2024-01-15 10:30:00

Connecting to database...
Connected successfully!

Fetching all companies...
Found 10 companies

Processing company: company-123
  Random limit selected: 7
  Found 7 interview(s) to update
  Updated interview interview-1: date = 2024-01-14 10:30:00
  Updated interview interview-2: date = 2024-01-13 10:30:00
  Updated interview interview-3: date = 2024-01-12 10:30:00
  Updated interview interview-4: date = 2024-01-11 10:30:00
  Updated interview interview-5: date = 2024-01-10 10:30:00
  Updated interview interview-6: date = 2024-01-09 10:30:00
  Updated interview interview-7: date = 2024-01-08 10:30:00
  Successfully updated 7 interview(s)

...

Committing changes to database...
Successfully committed all changes!

============================================================
Summary:
  Total companies processed: 10
  Total interviews updated: 75
============================================================
```

