#!/usr/bin/env python3
"""
Pre-Deployment Test Suite
Run this on your Raspberry Pi before enabling the cron job
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(name):
    """Print test name"""
    print(f"\n{BLUE}[TEST]{RESET} {name}")


def print_success(message):
    """Print success message"""
    print(f"  {GREEN}✓{RESET} {message}")


def print_error(message):
    """Print error message"""
    print(f"  {RED}✗{RESET} {message}")


def print_warning(message):
    """Print warning message"""
    print(f"  {YELLOW}⚠{RESET}  {message}")


async def test_imports():
    """Test that all required modules can be imported"""
    print_test("Testing imports...")
    
    modules = [
        ('services.email_service', 'EmailService'),
        ('services.download_service', 'RatingsDownloader'),
        ('services.daily_report_generator', 'DailyReportGenerator'),
        ('services.xlsx_parser', 'XlsxParser'),
        ('utils.config', 'current_config'),
        ('utils.logger', 'get_logger'),
    ]
    
    all_passed = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print_success(f"{module_name}.{class_name}")
        except ImportError as e:
            print_error(f"{module_name}.{class_name} - {str(e)}")
            all_passed = False
    
    return all_passed


async def test_configuration():
    """Test configuration settings"""
    print_test("Testing configuration...")
    
    try:
        from utils.config import current_config
        
        print_success(f"Config mode: {current_config.NAME}")
        print_success(f"Download dir: {current_config.DOWNLOAD_DIR}")
        print_success(f"Schema path: {current_config.SCHEMA}")
        
        # Check if paths exist
        if not current_config.DOWNLOAD_DIR.exists():
            print_warning(f"Download directory doesn't exist - creating it")
            current_config.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        schema_path = Path(current_config.SCHEMA)
        if not schema_path.exists():
            print_error(f"Schema file not found: {current_config.SCHEMA}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Configuration error: {str(e)}")
        return False


async def test_environment_variables():
    """Test environment variables"""
    print_test("Testing environment variables...")
    
    import os
    
    required_vars = ['GMAIL_ADDRESS', 'GMAIL_APP_PASSWORD']
    all_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != 'your-email@gmail.com' and value != 'your-16-char-app-password':
            print_success(f"{var} is set")
        else:
            print_error(f"{var} is not set or uses placeholder value")
            all_set = False
    
    return all_set


async def test_email_connection():
    """Test Gmail connection"""
    print_test("Testing Gmail connection...")
    
    try:
        from services.email_service import EmailService
        
        email_service = EmailService(use_yesterday=False)
        connected = email_service.connect()
        
        if connected:
            print_success("Connected to Gmail successfully")
            email_service.disconnect()
            return True
        else:
            print_error("Failed to connect to Gmail")
            return False
            
    except Exception as e:
        print_error(f"Email connection error: {str(e)}")
        return False


async def test_credentials_service():
    """Test credential fetching (won't actually fetch unless email exists)"""
    print_test("Testing credentials service...")
    
    try:
        from utils.config import current_config
        
        cred_service = current_config.get_credentials_service(use_yesterday=False)
        print_success(f"Credentials service type: {type(cred_service).__name__}")
        
        # Don't actually fetch - just verify service exists
        if hasattr(cred_service, 'fetch_ratings_credentials'):
            print_success("Service has fetch_ratings_credentials method")
            return True
        else:
            print_error("Service missing fetch_ratings_credentials method")
            return False
            
    except Exception as e:
        print_error(f"Credentials service error: {str(e)}")
        return False


async def test_version():
    """Test version information"""
    print_test("Testing version information...")
    
    try:
        from utils import version
        print_success(f"Version: {version.__version__}")
        print_success(f"Release: {version.__release_date__}")
        print_success(f"Description: {version.__description__}")
        return True
    except Exception as e:
        print_error(f"Version test failed: {str(e)}")
        return False


async def test_file_structure():
    """Test required files exist"""
    print_test("Testing file structure...")
    
    required_files = [
        'daily_ratings_automation.py',
        'requirements.txt',
        'core/mappings.json',
        'core/time_slots.json',
        'services/email_service.py',
        'services/download_service.py',
        'services/daily_report_generator.py',
        'utils/config.py',
        'utils/logger.py',
    ]
    
    all_exist = True
    for filepath in required_files:
        path = Path(filepath)
        if path.exists():
            print_success(filepath)
        else:
            print_error(f"Missing: {filepath}")
            all_exist = False
    
    return all_exist


async def test_log_directory():
    """Test log directory exists and is writable"""
    print_test("Testing log directory...")
    
    try:
        log_dir = Path.home() / 'ratings' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write
        test_file = log_dir / 'test.log'
        test_file.write_text(f"Test write at {datetime.now()}\n")
        
        if test_file.exists():
            print_success(f"Log directory writable: {log_dir}")
            test_file.unlink()  # Clean up
            return True
        else:
            print_error("Cannot write to log directory")
            return False
            
    except Exception as e:
        print_error(f"Log directory error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("="*60)
    print(f"{BLUE}TV Ratings Automation - Pre-Deployment Tests{RESET}")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Environment Variables", test_environment_variables),
        ("File Structure", test_file_structure),
        ("Log Directory", test_log_directory),
        ("Version", test_version),
        ("Credentials Service", test_credentials_service),
        ("Email Connection", test_email_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print(f"{BLUE}Test Summary{RESET}")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name:.<40} {status}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}✓ All tests passed! Ready for deployment.{RESET}\n")
        return 0
    else:
        print(f"\n{RED}✗ Some tests failed. Fix issues before deploying.{RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
