#!/usr/bin/env python3
"""
Test Runner for Ratings Automation

Runs the automation pipeline with stub services and test scenarios.
No network calls, no real emails - just scenario-driven testing.

Usage:
    python test_runner.py                     # Run all scenarios
    python test_runner.py happy_path          # Run specific scenario
    python test_runner.py --list              # List available scenarios
"""

import json
import os
import sys
from pathlib import Path

# Set test mode BEFORE any other imports
os.environ['ENV'] = 'test'

PROJECT_ROOT = Path(__file__).parent
SCENARIOS_FILE = PROJECT_ROOT / 'Data' / 'test_scenarios' / 'scenarios.json'


def load_scenarios() -> list[dict]:
    """Load all scenarios from scenarios.json."""
    with open(SCENARIOS_FILE) as f:
        data = json.load(f)
    return data.get("scenarios", [])


def list_scenarios() -> None:
    """Print available scenarios."""
    scenarios = load_scenarios()
    print("\nAvailable scenarios:")
    print("-" * 50)
    for s in scenarios:
        print(f"  {s['name']:<25} {s.get('description', '')}")
    print()


def run_scenario(scenario_name: str) -> int:
    """Run automation with a specific scenario.

    Args:
        scenario_name: Name of scenario to run

    Returns:
        Exit code from automation (0 = success)
    """
    os.environ['TEST_SCENARIO'] = scenario_name

    print(f"\n{'=' * 60}")
    print(f"SCENARIO: {scenario_name}")
    print('=' * 60)

    # Import after setting environment
    import asyncio
    import automation

    # Override retry settings for fast testing
    automation.MAX_RETRIES = 1
    automation.RETRY_INTERVAL = 0

    try:
        exit_code = asyncio.run(automation.main())
        return exit_code
    except Exception as e:
        print(f"ERROR: {e}")
        return -1


def run_all_scenarios() -> dict[str, int]:
    """Run all scenarios and collect results.

    Returns:
        Dict mapping scenario name to exit code
    """
    scenarios = load_scenarios()
    results = {}

    for scenario in scenarios:
        name = scenario['name']
        # Need to reload automation module for each scenario
        # to reset any module-level state
        if 'automation' in sys.modules:
            del sys.modules['automation']

        results[name] = run_scenario(name)

    return results


def print_summary(results: dict[str, int]) -> None:
    """Print test run summary."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    scenarios = load_scenarios()
    scenario_map = {s['name']: s for s in scenarios}

    for name, exit_code in results.items():
        expected = scenario_map.get(name, {}).get('expected_outcome', '?')
        status = "PASS" if exit_code == 0 else f"EXIT {exit_code}"
        print(f"  {name:<25} {status:<12} (expected: {expected})")

    print()


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--list':
            list_scenarios()
            return 0

        if arg == '--all':
            results = run_all_scenarios()
            print_summary(results)
            return 0 if all(code == 0 for code in results.values()) else 1

        # Run specific scenario
        return run_scenario(arg)

    # Default: run all scenarios
    results = run_all_scenarios()
    print_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
