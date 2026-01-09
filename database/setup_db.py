import sqlite3
import os

def init_database():
    """Initialize the database with schema and default data"""
    try:
        # Get the absolute path to the schema file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, 'schema.sql')
        db_path = os.path.join(current_dir, 'trading_sessions.db')
        
        # Read the schema file
        with open(schema_path, 'r') as f:
            schema = f.read()
            
        # Connect to database and execute schema
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        conn.commit()

                # # Insert common currency pairs
        # currency_pairs = [
        #     'AUDUSD', 'EURUSD', 'GBPUSD', 'USDCHF', 'USDJPY', 'USDCAD', 'AUDNZD', 'AUDCAD', 'AUDCHF', 'AUDJPY',
        #     'EURAUD', 'CHFJPY', 'EURGBP', 'EURNZD', 'EURCHF', 'EURJPY', 'EURCAD', 'GBPCHF', 'GBPJPY', 'CADCHF',
        #     'GBPCAD', 'CADJPY', 'AUDSGD', 'CHFSGD', 'XAUUSD', 'XAGUSD', 'XAUJPY', 'XAGJPY', 'XAUGBP', 'XAGGBP',
        #     'XAUCHF', 'XAUEUR', 'XAGEUR', 'BTCUSD', 'ETHUSD'
        # ]
        # Define currency pairs with categories - all from database
        currency_pairs = [
            # Most traded currency pairs
            ('EURUSD', 'mostTraded'), ('USDJPY', 'mostTraded'), ('GBPUSD', 'mostTraded'),
            ('AUDUSD', 'mostTraded'), ('USDCAD', 'mostTraded'), ('USDCHF', 'mostTraded'),
            ('NZDUSD', 'mostTraded'), ('EURJPY', 'mostTraded'), ('GBPJPY', 'mostTraded'),
            ('EURGBP', 'mostTraded'), ('AUDJPY', 'mostTraded'), ('EURCHF', 'mostTraded'),
            ('EURCAD', 'mostTraded'), ('EURAUD', 'mostTraded'), ('AUDNZD', 'mostTraded'),
            ('AUDCAD', 'mostTraded'), ('AUDCHF', 'mostTraded'), ('CHFJPY', 'mostTraded'),
            ('EURNZD', 'mostTraded'), ('GBPCHF', 'mostTraded'), ('GBPCAD', 'mostTraded'),
            ('CADJPY', 'mostTraded'), ('CADCHF', 'mostTraded'),
            # Additional FX pairs
            ('AUDSGD', 'mostTraded'), ('CHFSGD', 'mostTraded'),
            # Metals and commodities
            ('XAUUSD', 'metals'), ('XAGUSD', 'metals'), ('XAUJPY', 'metals'),
            ('XAUGBP', 'metals'), ('XAUCHF', 'metals'), ('XAUEUR', 'metals'),
            ('XAGEUR', 'metals'), ('XPTUSD', 'metals'), ('XPDUSD', 'metals'),
            ('XAUAUD', 'metals'), ('XAGAUD', 'metals'),
            # Cryptocurrencies
            ('BTCUSD', 'crypto'), ('ETHUSD', 'crypto'), ('BCHUSD', 'crypto'),
            ('LTCUSD', 'crypto'), ('XRPUSD', 'crypto'), ('XLMUSD', 'crypto'),
            ('ADAUSD', 'crypto'), ('XTZUSD', 'crypto'), ('DOGUSD', 'crypto'),
            ('UNIUSD', 'crypto'), ('BNBUSD', 'crypto'), ('DOTUSD', 'crypto'),
            ('LNKUSD', 'crypto'), ('SOLUSD', 'crypto'), ('AVXUSD', 'crypto'),
            ('KSMUSD', 'crypto'), ('GLMUSD', 'crypto'), ('MTCUSD', 'crypto')
        ]
        
        # Insert pairs with categories and store their IDs
        pair_ids = {}
        for pair, category in currency_pairs:
            cursor = conn.execute(
                'INSERT OR IGNORE INTO currency_pairs (symbol, category) VALUES (?, ?)',
                (pair, category)
            )
            conn.execute(
                'UPDATE currency_pairs SET is_active = 1, category = ? WHERE symbol = ?',
                (category, pair)
            )
            pair_ids[pair] = conn.execute('SELECT id FROM currency_pairs WHERE symbol = ?', (pair,)).fetchone()[0]
        
        # Get all session IDs
        sessions = conn.execute('SELECT id FROM trading_sessions').fetchall()
        
        # Associate all pairs with all sessions (initially neutral)
        for session in sessions:
            session_id = session[0]
            for pair_id in pair_ids.values():
                conn.execute('''
                    INSERT OR IGNORE INTO session_pairs 
                    (session_id, pair_id, trade_direction) 
                    VALUES (?, ?, 'neutral')
                ''', (session_id, pair_id))
        
        conn.commit()
        print("Database initialized successfully!")
        print(f"Database location: {db_path}")
        
        # Verify the setup
        cursor = conn.cursor()
        
        # Check sessions
        cursor.execute('SELECT COUNT(*) FROM trading_sessions')
        session_count = cursor.fetchone()[0]
        print(f"Trading sessions created: {session_count}")
        
        # Check currency pairs
        cursor.execute('SELECT COUNT(*) FROM currency_pairs')
        pair_count = cursor.fetchone()[0]
        print(f"Currency pairs created: {pair_count}")
        
        # Check session pairs
        cursor.execute('SELECT COUNT(*) FROM session_pairs')
        session_pairs_count = cursor.fetchone()[0]
        print(f"Session-pair associations created: {session_pairs_count}")
        
        # Print some sample data
        print("\nSample session pairs:")
        cursor.execute('''
            SELECT ts.name, cp.symbol, sp.trade_direction
            FROM session_pairs sp
            JOIN trading_sessions ts ON ts.id = sp.session_id
            JOIN currency_pairs cp ON cp.id = sp.pair_id
            LIMIT 5
        ''')
        for row in cursor.fetchall():
            print(f"Session: {row[0]}, Pair: {row[1]}, Direction: {row[2]}")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_database() 