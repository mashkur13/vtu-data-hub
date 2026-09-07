import sqlite3
import hashlib
from config import Config

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect('vtu.db')
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_connection()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        phone TEXT,
        role TEXT DEFAULT 'customer',
        is_active INTEGER DEFAULT 1
    )''')
    
    # Wallets table
    c.execute('''CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        balance REAL DEFAULT 0
    )''')
    
    # Networks table
    c.execute('''CREATE TABLE IF NOT EXISTS networks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        color TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    
    # Data plans table
    c.execute('''CREATE TABLE IF NOT EXISTS data_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        network_id INTEGER,
        data_amount TEXT,
        validity TEXT,
        price REAL,
        is_active INTEGER DEFAULT 1
    )''')
    
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount REAL,
        reference TEXT,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Check if admin exists
    c.execute('SELECT id FROM users WHERE role = "admin"')
    if not c.fetchone():
        # Create admin user
        admin_password = hashlib.sha256(Config.ADMIN_PASSWORD.encode()).hexdigest()
        c.execute('INSERT INTO users (username, email, password, phone, role) VALUES (?, ?, ?, ?, ?)',
                 ('Admin', Config.ADMIN_EMAIL, admin_password, '08000000000', 'admin'))
        admin_id = c.lastrowid
        c.execute('INSERT INTO wallets (user_id, balance) VALUES (?, 0)', (admin_id,))
        
        # Add default networks
        networks = [
            ('MTN', '#FFCC00'),
            ('Airtel', '#ED1C24'),
            ('Glo', '#00A651'),
            ('9mobile', '#00A88E')
        ]
        
        network_ids = {}
        for name, color in networks:
            c.execute('INSERT INTO networks (name, color) VALUES (?, ?)', (name, color))
            network_ids[name] = c.lastrowid
        
        # Add default plans
        plans = [
            (network_ids['MTN'], '500MB', '7 days', 150),
            (network_ids['MTN'], '1GB', '7 days', 300),
            (network_ids['MTN'], '2GB', '14 days', 500),
            (network_ids['MTN'], '5GB', '30 days', 1200),
            (network_ids['Airtel'], '750MB', '7 days', 200),
            (network_ids['Airtel'], '1.5GB', '14 days', 500),
            (network_ids['Airtel'], '3GB', '30 days', 800),
            (network_ids['Glo'], '1GB', '7 days', 200),
            (network_ids['Glo'], '2GB', '14 days', 500),
            (network_ids['Glo'], '10GB', '30 days', 2000),
            (network_ids['9mobile'], '500MB', '7 days', 150),
            (network_ids['9mobile'], '1GB', '7 days', 300),
        ]
        
        for network_id, data, validity, price in plans:
            c.execute('INSERT INTO data_plans (network_id, data_amount, validity, price) VALUES (?, ?, ?, ?)',
                     (network_id, data, validity, price))
    
    conn.commit()
    conn.close()
