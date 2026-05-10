import sqlite3

db_path = "axon_trading.db"
try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # Add columns if they don't exist
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN reason TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN criteria TEXT")
        except:
            pass
        conn.commit()
    print("Database Migration Successful.")
except Exception as e:
    print(f"Migration Failed: {e}")
