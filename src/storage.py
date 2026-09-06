import sqlite3, json

def get_connection():
    con = sqlite3.connect("data/opportunities.db")
    
    return con

def init_db():
    con = get_connection()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS opportunities(id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, source_id INTEGER, title TEXT, url TEXT, location TEXT, deadline_text TEXT, prize_amount TEXT, organization TEXT, themes TEXT, UNIQUE(source, source_id))")
    con.commit()

def save_opportunity(opp: dict):
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO opportunities(source, source_id, title, url, location, deadline_text, prize_amount, organization, themes) VALUES(?,?,?,?,?,?,?,?,?)",
        (opp["source"], opp["source_id"],opp["title"], opp["url"], opp["location"], opp["deadline_text"], opp["prize_amount"], opp["organization"], json.dumps(opp["themes"]))
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