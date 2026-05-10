import sqlite3

def repair_db():
    try:
        conn = sqlite3.connect('axon_trading.db')
        cursor = conn.cursor()
        
        # Ensure settings table exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                         (id INTEGER PRIMARY KEY, risk_pct REAL, trading_enabled INTEGER, symbols TEXT)''')
        
        # Check if record exists
        cursor.execute("SELECT count(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            print("Injected default settings.")
            cursor.execute("INSERT INTO settings (id, risk_pct, trading_enabled, symbols) VALUES (1, 1.0, 0, 'XAUUSDm,EURUSDm,GBPJPYm')")
        else:
            print("Settings record already exists.")
            
        conn.commit()
        conn.close()
        print("Database repair successful.")
    except Exception as e:
        print(f"Repair failed: {e}")

if __name__ == "__main__":
    repair_db()
