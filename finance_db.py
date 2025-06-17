import sqlite3

DB_NAME = "finance.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL,
            description TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_entry(user_id, entry_type, amount, description, date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entries (user_id, type, amount, description, date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, entry_type, amount, description, date))
    conn.commit()
    conn.close()

def get_all_entries(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT amount, description, date, id FROM entries
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_entry(user_id, entry_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id = ? AND user_id = ?", (entry_id, user_id))
    conn.commit()
    conn.close()


def get_user_entries_with_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, description, date FROM entries WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_entry(entry_id, new_amount, new_description):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE entries
        SET amount = ?, description = ?
        WHERE id = ?
    """, (new_amount, new_description, entry_id))
    conn.commit()
    conn.close()