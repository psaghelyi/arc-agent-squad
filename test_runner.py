#!/usr/bin/env python3
"""
Test runner for the GRC Agent Squad project.

This script provides an easy way to run different test suites.
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import os


def run_command(command, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def run_unit_tests():
    """Run unit tests."""
    return run_command(
        "python -m pytest tests/unit/ -v --tb=short",
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests."""
    return run_command(
        "python -m pytest tests/integration/ -v --tb=short",
        "Integration Tests"
    )


def run_all_tests():
    """Run all tests."""
    return run_command(
        "python -m pytest tests/ -v --tb=short",
        "All Tests"
    )


def run_tests_with_coverage():
    """Run tests with coverage report."""
    return run_command(
        "python -m pytest tests/ -v --tb=short --cov=src --cov-report=html --cov-report=term",
        "Tests with Coverage"
    )


def run_orchestrator_tests():
    """Run only orchestrator tests."""
    return run_command(
        "python -m pytest tests/unit/test_agent_orchestrator.py -v --tb=short",
        "Agent Orchestrator Tests"
    )


def run_chat_tests():
    """Run only chat integration tests."""
    return run_command(
        "python -m pytest tests/integration/test_chat_integration.py -v --tb=short",
        "Chat Integration Tests"
    )


def run_api_tests():
    """Run only API integration tests."""
    return run_command(
        "python -m pytest tests/integration/test_api_integration.py -v --tb=short",
        "API Integration Tests"
    )


def run_quick_tests():
    """Run a quick subset of tests."""
    success = True
    success &= run_command(
        "python -m pytest tests/unit/test_health.py -v --tb=short",
        "Health Check Tests"
    )
    success &= run_command(
        "python -m pytest tests/unit/test_agent_orchestrator.py::TestGRCAgentSquad::test_list_agents -v --tb=short",
        "GRC Agent Squad Test"
    )
    success &= run_command(
        "python -m pytest tests/integration/test_chat_integration.py::TestChatIntegration::test_simple_chat_flow -v --tb=short",
        "Simple Chat Test"
    )
    return success


def run_e2e_tests():
    """Run end-to-end tests with real AWS services."""
    print("🌐 Running end-to-end tests...")
    print("⚠️  These tests require AWS SSO credentials and will make real API calls")
    print("⚠️  Make sure you're logged in with: aws sso login --profile acl-playground")
    return run_command(
        "python -m pytest tests/e2e/ -v --tb=short -m e2e --timeout=300",
        "End-to-End Tests"
    )


def run_watch_tests():
    """Run tests in watch mode for development."""
    print("👀 Running tests in watch mode...")
    try:
        cmd = [sys.executable, "-m", "pytest_watch", "tests/unit/", "tests/integration/"]
        return subprocess.run(cmd).returncode
    except FileNotFoundError:
        print("❌ pytest-watch not installed. Install with: pip install pytest-watch")
        return 1


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Test runner for GRC Agent Squad")
    parser.add_argument(
        "test_type",
        choices=["all", "unit", "integration", "e2e", "coverage", "watch"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true", 
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 GRC Agent Squad Test Runner")
    
    success = True
    if args.test_type == "all":
        success = run_all_tests()
    elif args.test_type == "unit":
        success = run_unit_tests()
    elif args.test_type == "integration":
        success = run_integration_tests()
    elif args.test_type == "e2e":
        success = run_e2e_tests()
    elif args.test_type == "coverage":
        success = run_tests_with_coverage()
    elif args.test_type == "watch":
        success = run_watch_tests()
    
    exit_code = 0 if success else 1
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!")
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 