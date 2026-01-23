import sqlite3
import os
import sys

# Add database directory to path to import msgpack_loader
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from msgpack_loader import SymbolLoader, get_fallback_symbols

def update_database_from_msgpack(msgpack_path=None, db_path=None):
    """
    Update currency pairs in database from centralized msgpack file.
    This reusable function follows DRY principle and can be called from:
    - init_database() for initial setup
    - retrieve_symbols.bat after symbol retrieval
    - API endpoint for manual refresh
    
    Args:
        msgpack_path: Path to msgpack file. If None, uses default location.
        db_path: Path to database file. If None, uses default location.
    
    Returns:
        dict: Result with status, message, symbols_count, and statistics
    """
    if msgpack_path is None:
        msgpack_path = os.path.join(current_dir, 'mt5_symbols.msgpack')
    if db_path is None:
        db_path = os.path.join(current_dir, 'trading_sessions.db')
    
    try:
        # Load symbols from msgpack
        loader = SymbolLoader(msgpack_path)
        currency_pairs = loader.get_all_symbols(db_format=True)
        
        # If msgpack file doesn't exist or loading failed, use fallback
        if not currency_pairs:
            print("[WARNING] Failed to load from msgpack file, using fallback symbols")
            currency_pairs = get_fallback_symbols()
            # Convert fallback categories to db format
            db_format_mapping = {
                'most_traded': 'mostTraded',
                'metals': 'metals',
                'crypto': 'crypto',
                'other': 'other',
                'commodities': 'other'
            }
            currency_pairs = [(symbol, db_format_mapping.get(cat, 'other')) for symbol, cat in currency_pairs]
        
        if not currency_pairs:
            return {
                'status': 'error',
                'error': 'No symbols to update. Please run retrieve_symbols.bat first.'
            }
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        # Set row_factory to Row for dictionary-like access
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            
            # Ensure schema exists (in case database doesn't exist yet)
            schema_path = os.path.join(current_dir, 'schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema = f.read()
                conn.executescript(schema)
                conn.commit()
            
            # Get existing pair IDs to preserve session mappings
            existing_pairs = {}
            for row in cursor.execute('SELECT id, symbol FROM currency_pairs').fetchall():
                existing_pairs[row['symbol']] = row['id']
            
            # Insert or update pairs
            pair_ids = {}
            new_count = 0
            updated_count = 0
            for symbol, category in currency_pairs:
                if symbol in existing_pairs:
                    # Update existing pair
                    pair_id = existing_pairs[symbol]
                    cursor.execute(
                        'UPDATE currency_pairs SET is_active = 1, category = ? WHERE id = ?',
                        (category, pair_id)
                    )
                    pair_ids[symbol] = pair_id
                    updated_count += 1
                else:
                    # Insert new pair
                    cursor.execute(
                        'INSERT INTO currency_pairs (symbol, category, is_active) VALUES (?, ?, 1)',
                        (symbol, category)
                    )
                    pair_id = cursor.lastrowid
                    pair_ids[symbol] = pair_id
                    new_count += 1
                    
                    # Associate new pair with all existing sessions
                    session_ids = [row['id'] for row in cursor.execute('SELECT id FROM trading_sessions').fetchall()]
                    for session_id in session_ids:
                        cursor.execute(
                            'INSERT OR IGNORE INTO session_pairs (session_id, pair_id, trade_direction) VALUES (?, ?, ?)',
                            (session_id, pair_id, 'neutral')
                        )
            
            # Deactivate pairs that are no longer in msgpack (but don't delete them)
            all_symbols = set(symbol for symbol, _ in currency_pairs)
            deactivated_count = 0
            for symbol, pair_id in existing_pairs.items():
                if symbol not in all_symbols:
                    cursor.execute(
                        'UPDATE currency_pairs SET is_active = 0 WHERE id = ?',
                        (pair_id,)
                    )
                    deactivated_count += 1
            
            conn.commit()
            
            return {
                'status': 'success',
                'message': f'Successfully updated {len(currency_pairs)} symbols in database',
                'symbols_count': len(currency_pairs),
                'new_symbols': new_count,
                'updated_symbols': updated_count,
                'deactivated_symbols': deactivated_count
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        import traceback
        error_msg = f'Failed to update database: {str(e)}'
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        return {
            'status': 'error',
            'error': error_msg
        }


def init_database():
    """Initialize the database with schema and default data"""
    try:
        # Get the absolute path to the schema file
        schema_path = os.path.join(current_dir, 'schema.sql')
        db_path = os.path.join(current_dir, 'trading_sessions.db')
        msgpack_path = os.path.join(current_dir, 'mt5_symbols.msgpack')
        
        # Read the schema file
        with open(schema_path, 'r') as f:
            schema = f.read()
            
        # Connect to database and execute schema
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()  # Close before calling update function

        # Use shared function to update symbols from msgpack (DRY principle)
        print("[INFO] Loading symbols from mt5_symbols.msgpack...")
        update_result = update_database_from_msgpack(msgpack_path, db_path)
        
        if update_result['status'] == 'error':
            print(f"[WARNING] {update_result.get('error', 'Failed to update from msgpack')}")
            print("[INFO] Database schema created, but symbols not loaded.")
            return
        
        print(f"[INFO] {update_result['message']}")
        print(f"[INFO] Total symbols: {update_result['symbols_count']}")
        
        # Reconnect to verify and ensure all session mappings exist
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        try:
            cursor = conn.cursor()
            
            # Get all pair IDs and session IDs to ensure mappings
            pair_ids = {}
            for row in cursor.execute('SELECT id, symbol FROM currency_pairs WHERE is_active = 1').fetchall():
                pair_ids[row['symbol']] = row['id']
            
            sessions = cursor.execute('SELECT id FROM trading_sessions').fetchall()
            
            # Ensure all pairs are associated with all sessions
            for session in sessions:
                session_id = session['id'] if isinstance(session, sqlite3.Row) else session[0]
                for pair_id in pair_ids.values():
                    cursor.execute('''
                        INSERT OR IGNORE INTO session_pairs 
                        (session_id, pair_id, trade_direction) 
                        VALUES (?, ?, 'neutral')
                    ''', (session_id, pair_id))
            
            conn.commit()
            
            print("Database initialized successfully!")
            print(f"Database location: {db_path}")
            
            # Verify the setup
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
                print(f"Session: {row['name']}, Pair: {row['symbol']}, Direction: {row['trade_direction']}")
        finally:
            conn.close()
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

def update_symbols():
    """Standalone function to update symbols from msgpack (called from batch script).
    Uses the shared update_database_from_msgpack() function following DRY principle."""
    result = update_database_from_msgpack()
    if result['status'] == 'success':
        print(f"\n[SUCCESS] {result['message']}")
        print(f"  - Total symbols: {result['symbols_count']}")
        print(f"  - New symbols: {result.get('new_symbols', 0)}")
        print(f"  - Updated symbols: {result.get('updated_symbols', 0)}")
        print(f"  - Deactivated symbols: {result.get('deactivated_symbols', 0)}")
        return 0
    else:
        print(f"\n[ERROR] {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        # Called from batch script to update symbols
        exit_code = update_symbols()
        sys.exit(exit_code)
    else:
        # Normal initialization
        init_database() 