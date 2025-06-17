import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "finance.db"

def export_to_excel(user_id):
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT type, amount, description, date
        FROM entries
        WHERE user_id = ?
        ORDER BY date DESC
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()

    if df.empty:
        df = pd.DataFrame(columns=["type", "amount", "description", "date"])

    file_name = f"finance_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(file_name, index=False)
    return file_name
