"""
Migration script to add category column to currency_pairs table
Run this if you have an existing database that needs the category column
"""
import sqlite3
import os

def migrate_add_category():
    """Add category column to existing currency_pairs table"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'trading_sessions.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(currency_pairs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'category' in columns:
            print("Category column already exists. Skipping migration.")
            return
        
        # Add category column
        print("Adding category column to currency_pairs table...")
        cursor.execute('''
            ALTER TABLE currency_pairs 
            ADD COLUMN category TEXT CHECK(category IN ('mostTraded', 'metals', 'crypto', 'other')) DEFAULT 'other'
        ''')
        
        # Update categories based on symbol patterns
        # Most traded pairs
        most_traded = [
            'EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD', 'USDCHF',
            'NZDUSD', 'EURJPY', 'GBPJPY', 'EURGBP', 'AUDJPY', 'EURCHF',
            'EURCAD', 'EURAUD', 'AUDNZD', 'AUDCAD', 'AUDCHF', 'CHFJPY',
            'EURNZD', 'GBPCHF', 'GBPCAD', 'CADJPY', 'CADCHF',
            'AUDSGD', 'CHFSGD'
        ]
        
        # Metals
        metals = [
            'XAUUSD', 'XAGUSD', 'XAUJPY', 'XAUGBP', 'XAUCHF', 'XAUEUR',
            'XAGEUR', 'XPTUSD', 'XPDUSD', 'XAUAUD', 'XAGAUD'
        ]
        
        # Cryptocurrencies
        crypto = [
            'BTCUSD', 'ETHUSD', 'BCHUSD', 'LTCUSD', 'XRPUSD', 'XLMUSD',
            'ADAUSD', 'XTZUSD', 'DOGUSD', 'UNIUSD', 'BNBUSD', 'DOTUSD',
            'LNKUSD', 'SOLUSD', 'AVXUSD', 'KSMUSD', 'GLMUSD', 'MTCUSD'
        ]
        
        # Update categories
        for symbol in most_traded:
            cursor.execute('UPDATE currency_pairs SET category = ? WHERE symbol = ?', ('mostTraded', symbol))
        
        for symbol in metals:
            cursor.execute('UPDATE currency_pairs SET category = ? WHERE symbol = ?', ('metals', symbol))
        
        for symbol in crypto:
            cursor.execute('UPDATE currency_pairs SET category = ? WHERE symbol = ?', ('crypto', symbol))
        
        # Set default for any remaining pairs
        cursor.execute("UPDATE currency_pairs SET category = 'other' WHERE category IS NULL OR category = ''")
        
        conn.commit()
        print("Migration completed successfully!")
        print(f"Updated categories for currency pairs in {db_path}")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_category()
