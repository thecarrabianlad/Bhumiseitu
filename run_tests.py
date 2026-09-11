"""
run_tests.py
------------
A minimal test runner used ONLY in this sandbox because it has no
network access to `pip install pytest`. It discovers every function
named test_* inside tests/test_*.py and runs it, reporting pass/fail
exactly like pytest would.

On your own machine, once you run `pip install -r requirements.txt`,
just use the real `pytest` command instead -- these test files are
completely standard and need no changes to run under real pytest.
"""

import importlib
import sys
import traceback
from pathlib import Path

TEST_DIR = Path(__file__).parent / "tests"


def discover_test_modules():
    modules = []
    for path in sorted(TEST_DIR.glob("test_*.py")):
        module_name = f"tests.{path.stem}"
        modules.append(module_name)
    return modules


def main():
    sys.path.insert(0, str(Path(__file__).parent))
    total = 0
    passed = 0
    failures = []

    for module_name in discover_test_modules():
        module = importlib.import_module(module_name)
        test_functions = [
            getattr(module, name) for name in dir(module)
            if name.startswith("test_") and callable(getattr(module, name))
        ]
        for func in test_functions:
            total += 1
            test_id = f"{module_name}.{func.__name__}"
            try:
                func()
                passed += 1
                print(f"PASSED  {test_id}")
            except Exception:
                failures.append((test_id, traceback.format_exc()))
                print(f"FAILED  {test_id}")

    print("\n" + "=" * 60)
    print(f"{passed}/{total} tests passed")
    if failures:
        print("\nFailure details:\n")
        for test_id, tb in failures:
            print(f"--- {test_id} ---\n{tb}")
        sys.exit(1)
    else:
        print("All tests passed.")


if __name__ == "__main__":
    main()
