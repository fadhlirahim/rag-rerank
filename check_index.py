import os
import lancedb
from dotenv import load_dotenv

# Attempt to import settings, handle if not found in a typical script environment
try:
    from app.core import settings
    LANCEDB_DATABASE_PATH = settings.LANCEDB_DATABASE_PATH
    LANCEDB_TABLE_NAME = settings.LANCEDB_TABLE_NAME
except ImportError:
    print("Could not import 'app.core.settings'.")
    print("Please ensure this script is run in an environment where 'app' module is accessible,")
    print("or set LANCEDB_DATABASE_PATH and LANCEDB_TABLE_NAME environment variables as fallback.")
    LANCEDB_DATABASE_PATH = os.getenv("LANCEDB_DATABASE_PATH", "./.lancedb") # Default fallback
    LANCEDB_TABLE_NAME = os.getenv("LANCEDB_TABLE_NAME", "my_table") # Default fallback

# Load environment variables from .env file.
# Useful if running standalone and .env contains LANCEDB_PATH or other relevant vars.
load_dotenv(override=True)

# If settings were imported, they take precedence. Otherwise, env vars or defaults are used.
if 'settings' in locals() and hasattr(settings, 'LANCEDB_DATABASE_PATH'):
    LANCEDB_DATABASE_PATH = settings.LANCEDB_DATABASE_PATH
if 'settings' in locals() and hasattr(settings, 'LANCEDB_TABLE_NAME'):
    LANCEDB_TABLE_NAME = settings.LANCEDB_TABLE_NAME


print("--- LanceDB Index Check Utility ---")
print(f"Attempting to connect to LanceDB at path: {LANCEDB_DATABASE_PATH}")

try:
    db = lancedb.connect(LANCEDB_DATABASE_PATH)
    print(f"Successfully connected to database director at: {LANCEDB_DATABASE_PATH}")

    print(f"Attempting to open table: {LANCEDB_TABLE_NAME}...")
    table = db.open_table(LANCEDB_TABLE_NAME)
    print(f"Table '{LANCEDB_TABLE_NAME}' opened successfully.")

    print(f"\n--- Table Information ---")
    print(f"Table Name: {table.name}") # Use table.name from the opened table object

    record_count = len(table)
    print(f"Total vector count: {record_count}")

    schema = table.schema
    print(f"Schema: {schema}")

    if record_count > 0:
        print("\n--- Sample Data (first up to 3 records) ---")
        try:
            sample_data = table.limit(3).to_list()
            for i, record in enumerate(sample_data):
                record_display = {}
                for k, v in record.items():
                    if k == 'vector' and isinstance(v, list) and len(v) > 10:
                        record_display[k] = str(v[:10]) + "... (truncated)"
                    else:
                        record_display[k] = v
                print(f"Record {i+1}: {record_display}")
        except Exception as e:
            print(f"Could not retrieve or display sample data: {e}")
    else:
        print("Table is empty. No sample data to display.")

except FileNotFoundError:
    print(f"\nERROR: LanceDB table '{LANCEDB_TABLE_NAME}' not found in database at '{LANCEDB_DATABASE_PATH}'.")
    print("Please ensure the table name is correct and data has been ingested.")
except lancedb.error.LanceDBError as le:
    print(f"\nERROR: A LanceDB specific error occurred: {le}")
    print("This could be due to an issue with the database files or configuration.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    print("Please check the LanceDB path, table name, and database integrity.")

print("\n--- Check Complete ---")
