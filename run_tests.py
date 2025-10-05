"""
Test runner script for comprehensive testing and coverage reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import time

def run_command(command, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    if result.stdout:
        print("\nSTDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    return result

def install_test_dependencies():
    """Install required test dependencies"""
    dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "pytest-asyncio>=0.21.0",
        "coverage>=7.0.0"
    ]
    
    for dep in dependencies:
        result = run_command(f"pip install {dep}", f"Installing {dep}")
        if result.returncode != 0:
            print(f"Failed to install {dep}")
            return False
    
    return True

def run_individual_tests():
    """Run individual test files"""
    test_files = [
        "test_security_utils.py",
        "test_error_handling.py",
        "test_cache_system.py",
        "test_health_checks.py",
        "test_structured_logging.py",
        "test_config_validation.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        if Path(test_file).exists():
            result = run_command(
                f"python -m pytest {test_file} -v",
                f"Running tests in {test_file}"
            )
            results[test_file] = result.returncode == 0
        else:
            print(f"Warning: {test_file} not found")
            results[test_file] = False
    
    return results

def run_all_tests_with_coverage():
    """Run all tests with coverage reporting"""
    modules_to_cover = [
        "security_utils",
        "error_handling", 
        "cache_system",
        "health_checks",
        "structured_logging",
        "config_validation"
    ]
    
    coverage_args = " ".join([f"--cov={module}" for module in modules_to_cover])
    
    command = f"python -m pytest test_*.py {coverage_args} --cov-report=html --cov-report=term-missing --cov-report=xml -v"
    
    result = run_command(command, "Running all tests with coverage")
    return result.returncode == 0

def run_performance_tests():
    """Run performance-focused tests"""
    command = "python -m pytest test_*.py -k 'performance or benchmark' -v"
    result = run_command(command, "Running performance tests")
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests"""
    command = "python -m pytest test_*.py -k 'integration' -v"
    result = run_command(command, "Running integration tests")
    return result.returncode == 0

def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT")
    print("="*80)
    
    # Check if coverage report exists
    if Path("htmlcov/index.html").exists():
        print("\nCoverage report generated: htmlcov/index.html")
        print("Open this file in a browser to view detailed coverage information")
    
    if Path("coverage.xml").exists():
        print("XML coverage report: coverage.xml")
    
    # List test files and their status
    test_files = list(Path(".").glob("test_*.py"))
    print(f"\nTest files found: {len(test_files)}")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # List modules being tested
    modules = [
        "security_utils.py",
        "error_handling.py",
        "cache_system.py", 
        "health_checks.py",
        "structured_logging.py",
        "config_validation.py"
    ]
    
    print(f"\nModules under test: {len(modules)}")
    for module in modules:
        status = "✓" if Path(module).exists() else "✗"
        print(f"  {status} {module}")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner")
    parser.add_argument("--install-deps", action="store_true", 
                       help="Install test dependencies")
    parser.add_argument("--individual", action="store_true",
                       help="Run individual test files")
    parser.add_argument("--coverage", action="store_true",
                       help="Run all tests with coverage")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests only")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests only")
    parser.add_argument("--all", action="store_true",
                       help="Run all test suites")
    parser.add_argument("--report", action="store_true",
                       help="Generate test report")
    
    args = parser.parse_args()
    
    # If no specific arguments, run all tests with coverage
    if not any([args.install_deps, args.individual, args.coverage, 
                args.performance, args.integration, args.all, args.report]):
        args.all = True
    
    success = True
    
    try:
        if args.install_deps or args.all:
            print("Installing test dependencies...")
            if not install_test_dependencies():
                success = False
                print("Failed to install dependencies")
        
        if args.individual or args.all:
            print("\nRunning individual tests...")
            results = run_individual_tests()
            if not all(results.values()):
                success = False
                print("Some individual tests failed:")
                for test_file, passed in results.items():
                    status = "PASS" if passed else "FAIL"
                    print(f"  {test_file}: {status}")
        
        if args.coverage or args.all:
            print("\nRunning tests with coverage...")
            if not run_all_tests_with_coverage():
                success = False
                print("Coverage tests failed")
        
        if args.performance:
            print("\nRunning performance tests...")
            if not run_performance_tests():
                success = False
                print("Performance tests failed")
        
        if args.integration:
            print("\nRunning integration tests...")
            if not run_integration_tests():
                success = False
                print("Integration tests failed")
        
        if args.report or args.all:
            generate_test_report()
        
        # Final summary
        print("\n" + "="*80)
        if success:
            print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        else:
            print("❌ SOME TESTS FAILED - CHECK OUTPUT ABOVE")
        print("="*80)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)