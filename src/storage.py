import sqlite3, json
from datetime import date

def get_connection():
    con = sqlite3.connect("data/opportunities.db")
    
    return con

def init_db():
    con = get_connection()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS opportunities(id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, source_id INTEGER, title TEXT, url TEXT, location TEXT, deadline_text TEXT,deadline_date TEXT, prize_amount TEXT, organization TEXT, themes TEXT, UNIQUE(source, source_id))")
    # Migrations for databases created before these columns existed. Each fails
    # harmlessly with "duplicate column name" once it has already been applied.
    for column in ("deadline_date TEXT", "notified_at TEXT"):
        try:
            cur.execute(f"ALTER TABLE opportunities ADD COLUMN {column}")
        except sqlite3.OperationalError:
            pass

    con.commit()

def save_opportunity(opp: dict):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO opportunities(source, source_id, title, url, location, deadline_text, deadline_date, prize_amount, organization, themes) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (opp["source"], opp["source_id"],opp["title"], opp["url"], opp["location"], opp["deadline_text"], opp["deadline_date"], opp["prize_amount"], opp["organization"], json.dumps(opp["themes"]))
    )
    con.commit()

def get_all_opportunities():
    con = get_connection()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    cur.execute("SELECT * FROM opportunities")
    rows = cur.fetchall()

    result = []
    for row in rows:
        opp = dict(row)
        opp["themes"] = json.loads(opp["themes"])
        result.append(opp)

    return result

def get_unnotified_opportunities():
    """Active opportunities that have not been sent in a digest yet."""
    con = get_connection()
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM opportunities "
        "WHERE deadline_date >= ? AND notified_at IS NULL "
        "ORDER BY deadline_date",
        (date.today().isoformat(),)
    )

    result = []
    for row in cur.fetchall():
        opp = dict(row)
        opp["themes"] = json.loads(opp["themes"])
        result.append(opp)

    return result


def mark_notified(opportunities):
    """Stamp opportunities as sent, so the next digest does not repeat them."""
    con = get_connection()
    cur = con.cursor()

    now = date.today().isoformat()
    cur.executemany(
        "UPDATE opportunities SET notified_at = ? WHERE id = ?",
        [(now, opp["id"]) for opp in opportunities]
    )

    con.commit()
    return cur.rowcount


def get_active_opportunities():
    con = get_connection()
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM opportunities WHERE deadline_date >= ? ORDER BY deadline_date",
        (date.today().isoformat(),)
    )
    rows = cur.fetchall()

    result = []
    for row in rows:
        opp = dict(row)
        opp["themes"] = json.loads(opp["themes"])
        result.append(opp)

    return result