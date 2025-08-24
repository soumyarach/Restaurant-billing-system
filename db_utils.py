import os
import sqlite3
import csv

# Paths — ensure these match your project structure
DB_DIR = os.path.join("db")
DB_PATH = os.path.join(DB_DIR, "restaurant.db")
DATA_DIR = os.path.join("data")
MENU_CSV = os.path.join(DATA_DIR, "menu.csv")

def ensure_db():
    """Ensure DB directory exists and the menu table is created."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            itemname TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            category TEXT,
            gst REAL DEFAULT 0.05
        );
    """)
    conn.commit()
    conn.close()

def populate_menu_from_csv():
    """Populate 'menu' table from data/menu.csv, if available."""
    ensure_db()
    if not os.path.exists(MENU_CSV):
        print(f"CSV file {MENU_CSV} not found. Please add a menu CSV.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open(MENU_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO menu (itemname, price, category, gst)
                    VALUES (?, ?, ?, ?);
                """, (
                    row.get('itemname', '0').strip(),
                    float(row.get('price', '0')),
                    row.get('category', '0').strip(),
                    float(row.get('gst', 0.05))
                ))
            except Exception as e:
                print("Error inserting row:", row, "—", e)
    conn.commit()
    conn.close()

if __name__== "_main_":
    ensure_db()
    populate_menu_from_csv()
    print("Database and menu setup complete.")