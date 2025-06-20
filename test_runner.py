#!/usr/bin/env python3
"""
Test runner for the Voice Agent Swarm project.

This script provides an easy way to run different test suites.
"""

import sys
import subprocess
import argparse
from pathlib import Path


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
        "python -m pytest tests/unit/test_agent_orchestrator.py::TestAgentOrchestrator::test_create_agent -v --tb=short",
        "Agent Creation Test"
    )
    success &= run_command(
        "python -m pytest tests/integration/test_chat_integration.py::TestChatIntegration::test_simple_chat_flow -v --tb=short",
        "Simple Chat Test"
    )
    return success


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Voice Agent Swarm Test Runner")
    parser.add_argument(
        "test_type",
        choices=[
            "unit", "integration", "all", "coverage", 
            "orchestrator", "chat", "api", "quick"
        ],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("src").exists() or not Path("tests").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment may not be activated")
        print("   Consider running: source venv/bin/activate")
    
    print("🚀 Voice Agent Swarm Test Runner")
    print(f"Running: {args.test_type} tests")
    
    # Map test types to functions
    test_functions = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "all": run_all_tests,
        "coverage": run_tests_with_coverage,
        "orchestrator": run_orchestrator_tests,
        "chat": run_chat_tests,
        "api": run_api_tests,
        "quick": run_quick_tests
    }
    
    success = test_functions[args.test_type]()
    
    if success:
        print(f"\n🎉 All {args.test_type} tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Some {args.test_type} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 