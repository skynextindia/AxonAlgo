import sqlite3
import os

db_path = "axon_trading.db"

def migrate():
    if not os.path.exists(db_path):
        print("Database not found. Initializing fresh...")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(system_status)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'strategy_alignment' not in columns:
            print("Adding strategy_alignment column...")
            cursor.execute("ALTER TABLE system_status ADD COLUMN strategy_alignment TEXT DEFAULT '{}'")
            
        if 'current_indicators' not in columns:
            print("Adding current_indicators column...")
            cursor.execute("ALTER TABLE system_status ADD COLUMN current_indicators TEXT DEFAULT '{}'")
            
        conn.commit()
        conn.close()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
