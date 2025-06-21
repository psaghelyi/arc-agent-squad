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


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="GRC Agent Squad Test Runner")
    parser.add_argument(
        "test_type",
        choices=["quick", "unit", "integration", "orchestrator", "chat", "api", "all", "coverage"],
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
    
    # Map test types to functions
    test_functions = {
        "quick": run_quick_tests,
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "orchestrator": run_orchestrator_tests,
        "chat": run_chat_tests,
        "api": run_api_tests,
        "all": run_all_tests,
        "coverage": run_tests_with_coverage
    }
    
    success = test_functions[args.test_type]()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 