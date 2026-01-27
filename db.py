import sqlite3
import pandas as pd

DB_FILE = "auction.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Teams Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            name TEXT PRIMARY KEY,
            budget INTEGER,
            spent INTEGER DEFAULT 0
        )
    ''')
    
    # Players Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            status TEXT DEFAULT 'Unsold', -- Unsold, Sold
            sold_to TEXT,
            price INTEGER,
            is_current BOOLEAN DEFAULT 0,
            current_bid INTEGER DEFAULT 0,
            holding_team TEXT,
            FOREIGN KEY(sold_to) REFERENCES teams(name)
        )
    ''')

    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# --- User Operations ---
def create_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print("User created successfully")
        return True
    except sqlite3.IntegrityError:
        print("User already exist")
        return False
    finally:
        conn.close()

def check_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and row['password'] == password:
        return True
    return False

# --- Team Operations ---
def add_team(name, budget):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO teams (name, budget) VALUES (?, ?)", (name, budget))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_teams():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM teams", conn)
    conn.close()
    return df.to_dict('records')

def get_team_stats(team_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM teams WHERE name = ?", (team_name,))
    team = c.fetchone()
    
    # Get players
    players = pd.read_sql("SELECT * FROM players WHERE sold_to = ?", conn, params=(team_name,))
    conn.close()
    
    if team:
        return dict(team), players.to_dict('records')
    return None, []

# --- Player Operations ---
def add_player(name, role):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO players (name, role) VALUES (?, ?)", (name, role))
    conn.commit()
    conn.close()

def get_players():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM players", conn)
    conn.close()
    return df.to_dict('records')

def remove_player(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM players WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def set_current_player(name):
    conn = get_connection()
    c = conn.cursor()
    # Reset all current
    c.execute("UPDATE players SET is_current = 0")
    if name:
        c.execute("UPDATE players SET is_current = 1 WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def get_current_player():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE is_current = 1")
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_bid(player_name, team_name, amount):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE players 
            SET current_bid = ?, holding_team = ? 
            WHERE name = ?
        """, (amount, team_name, player_name))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def sell_player(player_name, team_name, price):
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Optimistic Locking: Only update if status is 'Unsold'
        # NOTE: We keep is_current = 1 so the "Sold" screen can be shown
        c.execute("""
            UPDATE players 
            SET status = 'Sold', sold_to = ?, price = ?, is_current = 1 
            WHERE name = ? AND status = 'Unsold'
        """, (team_name, price, player_name))
        
        if c.rowcount == 0:
            # Player was already sold or doesn't exist
            conn.rollback()
            return False
        
        # 2. Update Team Spent
        c.execute("UPDATE teams SET spent = spent + ? WHERE name = ?", (price, team_name))
        
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        return False
    finally:
        conn.close()

def dismiss_current_player():
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET is_current = 0 WHERE is_current = 1")
    conn.commit()
    conn.close()


def unsell_player(player_name):
    conn = get_connection()
    c = conn.cursor()
    
    # Get player details first to know price and team
    c.execute("SELECT sold_to, price FROM players WHERE name = ?", (player_name,))
    row = c.fetchone()
    
    if row:
        team_name = row['sold_to']
        price = row['price']
        
        try:
            # 1. Reset Player
            c.execute("""
                UPDATE players 
                SET status = 'Unsold', sold_to = NULL, price = NULL, is_current = 0
                WHERE name = ?
            """, (player_name,))
            
            # 2. Refund Team
            c.execute("UPDATE teams SET spent = spent - ? WHERE name = ?", (price, team_name))
            
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
    
    conn.close()
    return False

def reset_auction():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM players")
    c.execute("DELETE FROM teams")
    conn.commit()
    conn.close()
