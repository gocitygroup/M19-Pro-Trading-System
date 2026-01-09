#!/usr/bin/env python3
"""
Forex Trading System Launcher
Provides options to run different components of the autonomous system
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def print_banner():
    """Print system banner"""
    print("=" * 70)
    print("GOCITY TRADER TRADING PROFIT MONITORING")
    print("=" * 70)
    print("Gocity Group with ALGORITHMIC TRADING INVESTMENT")
    print("-" * 70)
    print("🏢 Managed by Gocity Managed Service s.r.l – VAT: 04886750274")
    print("✉️ Contact: invest@gocitygroup.org | services@gocitygroup.org | info@gocitygroup.org")
    print("=" * 70)
    print(f"Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def run_profit_monitor():
    """Run the profit monitor service"""
    print("Starting Profit Monitor Service...")
    print("- Autonomous operation")
    print("- Processes commands from web interface")
    print("- Updates database with position data")
    print("- Press Ctrl+C to stop")
    print()
    
    try:
        # Set PYTHONPATH environment variable to include project root
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, "src/scripts/run_profit_monitor.py"], check=True, env=env)
    except KeyboardInterrupt:
        print("\nProfit Monitor stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running profit monitor: {e}")

def run_enhanced_profit_monitor():
    """Run the enhanced profit monitor service with better performance"""
    print("Starting Enhanced Profit Monitor Service...")
    print("- Real-time profit/loss calculations")
    print("- Fast parallel position closing")
    print("- Optimized database operations")
    print("- Smart caching for better performance")
    print("- Asynchronous command processing")
    print("- Press Ctrl+C to stop")
    print()
    
    try:
        # Set PYTHONPATH environment variable to include project root
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, "src/scripts/run_enhanced_profit_monitor.py"], check=True, env=env)
    except KeyboardInterrupt:
        print("\nEnhanced Profit Monitor stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running enhanced profit monitor: {e}")

def run_web_interface():
    """Run the web interface"""
    print("Starting Web Interface...")
    print("- Real-time dashboard")
    print("- WebSocket communication")
    print("- Available at: http://localhost:44444")
    print("- Press Ctrl+C to stop")
    print()
    
    try:
        # Set PYTHONPATH environment variable to include project root
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, "src/web/app.py"], check=True, env=env)
    except KeyboardInterrupt:
        print("\nWeb Interface stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running web interface: {e}")

def run_both():
    """Run both components simultaneously"""
    print("Starting Both Components...")
    print("- This will run profit monitor and web interface together")
    print("- Both services will start in parallel")
    print("- Press Ctrl+C to stop both")
    print()
    
    import threading
    import time
    
    def run_monitor():
        try:
            # Set PYTHONPATH environment variable to include project root
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
            subprocess.run([sys.executable, "src/scripts/run_profit_monitor.py"], env=env)
        except Exception as e:
            print(f"Profit Monitor error: {e}")
    
    def run_web():
        time.sleep(2)  # Give monitor time to start
        try:
            # Set PYTHONPATH environment variable to include project root
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
            subprocess.run([sys.executable, "src/web/app.py"], env=env)
        except Exception as e:
            print(f"Web Interface error: {e}")
    
    # Start both in separate threads
    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    web_thread = threading.Thread(target=run_web, daemon=True)
    
    monitor_thread.start()
    web_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down both components...")

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        "src/core/profit_monitor.py",
        "src/web/app.py",
        "src/api/api_service.py",
        "src/config/config.py",
        "src/scripts/run_profit_monitor.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("ERROR: Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease ensure all system files are present.")
        return False
    
    return True

def show_status():
    """Show system status"""
    print("System Status:")
    print("-" * 40)
    
    # Check files
    files_ok = check_dependencies()
    print(f"Required Files: {'✓ OK' if files_ok else '✗ Missing'}")
    
    # Check database
    db_exists = os.path.exists("database/trading_sessions.db")
    print(f"Database File: {'✓ OK' if db_exists else '✗ Missing'}")
    
    # Check config
    config_exists = os.path.exists("src/config/config.json")
    print(f"Configuration: {'✓ OK' if config_exists else '✗ Missing'}")
    
    # Check commands directory
    commands_dir = os.path.exists("commands")
    print(f"Commands Directory: {'✓ OK' if commands_dir else '✗ Missing'}")
    
    # Check logs directory
    logs_dir = os.path.exists("logs")
    print(f"Logs Directory: {'✓ OK' if logs_dir else '✗ Missing'}")
    
    print("-" * 40)
    
    if not all([files_ok, db_exists, config_exists]):
        print("⚠️  System not ready. Please run setup first.")
    else:
        print("✅ System ready to launch!")

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description="Gocity Trader Trading Profit Monitoring Launcher")
    parser.add_argument("command", nargs="?", choices=["monitor", "enhanced", "web", "both", "status"], 
                       help="Component to run")
    parser.add_argument("--check", action="store_true", help="Check system status")
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.check or args.command == "status":
        show_status()
        return
    
    if not check_dependencies():
        print("Cannot start system due to missing dependencies.")
        return
    
    if args.command == "monitor":
        run_profit_monitor()
    elif args.command == "enhanced":
        run_enhanced_profit_monitor()
    elif args.command == "web":
        run_web_interface()
    elif args.command == "both":
        run_both()
    else:
        # Interactive menu
        print("Available Options:")
        print("1. Run Profit Monitor Only (Autonomous)")
        print("2. Run Enhanced Profit Monitor (Fast & Optimized)")
        print("3. Run Web Interface Only (Monitoring)")
        print("4. Run Both Components")
        print("5. Check System Status")
        print("6. Exit")
        print()
        
        while True:
            try:
                choice = input("Select option (1-6): ").strip()
                
                if choice == "1":
                    run_profit_monitor()
                    break
                elif choice == "2":
                    run_enhanced_profit_monitor()
                    break
                elif choice == "3":
                    run_web_interface()
                    break
                elif choice == "4":
                    run_both()
                    break
                elif choice == "5":
                    show_status()
                    break
                elif choice == "6":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break

if __name__ == "__main__":
    main() 