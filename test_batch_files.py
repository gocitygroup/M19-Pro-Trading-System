#!/usr/bin/env python3
"""
Interactive Test Script for G-SignalX-M19-Trading-System Batch Files
========================================================================
This script provides an interactive interface to test and verify:
1. Environment setup
2. Batch file functionality
3. Application entry points
4. Virtual environment configuration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}[✓]{Colors.RESET} {text}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}[✗]{Colors.RESET} {text}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {text}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}[i]{Colors.RESET} {text}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    path = Path(filepath)
    if path.exists():
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        print_success(f"{description}: {dirpath}")
        return True
    else:
        print_error(f"{description} not found: {dirpath}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print_success("Python version is compatible (3.8+)")
        return True
    else:
        print_error("Python 3.8 or higher is required")
        return False

def check_virtual_environment():
    """Check if virtual environment exists and is properly configured"""
    project_root = Path(__file__).parent
    venv_dir = project_root / ".venv"
    venv_activate = venv_dir / "Scripts" / "activate.bat"
    venv_python = venv_dir / "Scripts" / "python.exe"
    
    print_info("Checking virtual environment...")
    
    if not venv_dir.exists():
        print_warning("Virtual environment not found. Run setup_environment.bat first.")
        return False
    
    if not venv_activate.exists():
        print_error("Virtual environment activation script not found")
        return False
    
    if not venv_python.exists():
        print_error("Virtual environment Python executable not found")
        return False
    
    print_success("Virtual environment exists and is properly configured")
    return True

def check_batch_files():
    """Check if all batch files exist"""
    project_root = Path(__file__).parent
    batch_files = {
        "setup_environment.bat": "Environment setup script",
        "start_enhanced_system.bat": "Enhanced system launcher",
        "start_scouting_system.bat": "Scouting system launcher"
    }
    
    print_info("Checking batch files...")
    all_exist = True
    
    for filename, description in batch_files.items():
        filepath = project_root / filename
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_application_scripts():
    """Check if all application scripts exist"""
    project_root = Path(__file__).parent
    scripts = {
        "src/web/app.py": "Web Interface",
        "src/scripts/run_enhanced_profit_monitor.py": "Enhanced Profit Monitor",
        "src/scripts/ProfitScoutingBot.py": "Profit Scouting Bot",
        "src/scripts/MarketSessionTradingBot.py": "MarketSession Trading Bot",
        "src/scripts/run_gsignalx_automation_runner.py": "Automation Runner"
    }
    
    print_info("Checking application scripts...")
    all_exist = True
    
    for script_path, description in scripts.items():
        filepath = project_root / script_path
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_requirements_file():
    """Check if requirements.txt exists"""
    project_root = Path(__file__).parent
    requirements = project_root / "requirements.txt"
    
    print_info("Checking requirements.txt...")
    return check_file_exists(requirements, "Requirements file")

def check_logs_directory():
    """Check if logs directory exists"""
    project_root = Path(__file__).parent
    logs_dir = project_root / "logs"
    
    print_info("Checking logs directory...")
    if logs_dir.exists():
        print_success(f"Logs directory exists: {logs_dir}")
        return True
    else:
        print_warning("Logs directory does not exist (will be created by setup_environment.bat)")
        return True  # Not critical, will be created

def test_batch_file_syntax(batch_file):
    """Test batch file syntax (basic check)"""
    project_root = Path(__file__).parent
    filepath = project_root / batch_file
    
    if not filepath.exists():
        print_error(f"Batch file not found: {batch_file}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Basic checks
            if '@echo off' in content or '@echo on' in content:
                print_success(f"Batch file syntax check passed: {batch_file}")
                return True
            else:
                print_warning(f"Batch file may have syntax issues: {batch_file}")
                return True  # Not a critical error
    except Exception as e:
        print_error(f"Error reading batch file {batch_file}: {e}")
        return False

def run_interactive_menu():
    """Run interactive test menu"""
    while True:
        print_header("G-SignalX-M19-Trading-System - Batch File Test Suite")
        
        print("Select a test option:")
        print(f"{Colors.CYAN}1.{Colors.RESET} Run all checks")
        print(f"{Colors.CYAN}2.{Colors.RESET} Check Python environment")
        print(f"{Colors.CYAN}3.{Colors.RESET} Check virtual environment")
        print(f"{Colors.CYAN}4.{Colors.RESET} Check batch files")
        print(f"{Colors.CYAN}5.{Colors.RESET} Check application scripts")
        print(f"{Colors.CYAN}6.{Colors.RESET} Test batch file syntax")
        print(f"{Colors.CYAN}7.{Colors.RESET} Check project structure")
        print(f"{Colors.CYAN}8.{Colors.RESET} Exit")
        print()
        
        choice = input(f"{Colors.BOLD}Enter your choice (1-8): {Colors.RESET}").strip()
        
        if choice == '1':
            run_all_checks()
        elif choice == '2':
            check_python_version()
        elif choice == '3':
            check_virtual_environment()
        elif choice == '4':
            check_batch_files()
        elif choice == '5':
            check_application_scripts()
        elif choice == '6':
            test_all_batch_files()
        elif choice == '7':
            check_project_structure()
        elif choice == '8':
            print_success("Exiting test suite. Goodbye!")
            break
        else:
            print_error("Invalid choice. Please select 1-8.")
        
        input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")

def run_all_checks():
    """Run all checks"""
    print_header("Running All Checks")
    
    results = {
        "Python Version": check_python_version(),
        "Requirements File": check_requirements_file(),
        "Batch Files": check_batch_files(),
        "Application Scripts": check_application_scripts(),
        "Virtual Environment": check_virtual_environment(),
        "Logs Directory": check_logs_directory()
    }
    
    print_header("Test Results Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if result else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"{test_name}: {status}")
    
    print()
    if passed == total:
        print_success(f"All checks passed! ({passed}/{total})")
    else:
        print_warning(f"Some checks failed. ({passed}/{total} passed)")

def test_all_batch_files():
    """Test all batch files"""
    print_header("Testing Batch File Syntax")
    
    batch_files = [
        "setup_environment.bat",
        "start_enhanced_system.bat",
        "start_scouting_system.bat"
    ]
    
    for batch_file in batch_files:
        test_batch_file_syntax(batch_file)

def check_project_structure():
    """Check project structure"""
    print_header("Checking Project Structure")
    
    project_root = Path(__file__).parent
    required_dirs = [
        "src",
        "src/web",
        "src/scripts",
        "src/config",
        "src/core",
        "src/api",
        "src/automation",
        "database",
        "config"
    ]
    
    print_info("Checking required directories...")
    all_exist = True
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not check_directory_exists(full_path, f"Directory"):
            all_exist = False
    
    if all_exist:
        print_success("Project structure is valid")
    else:
        print_error("Some required directories are missing")

def main():
    """Main function"""
    # Check if running on Windows
    if platform.system() != 'Windows':
        print_error("This test script is designed for Windows systems")
        print_warning("Batch files (.bat) are Windows-specific")
        return
    
    # Run interactive menu
    try:
        run_interactive_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user.{Colors.RESET}")
    except Exception as e:
        print_error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
