"""
Automotive Test Runner & Verification Summary
Executes test cases and displays a clean verification dashboard.
"""

import sys
import pytest

def main():
    print("=" * 65)
    print("  AUTOMOTIVE HIL / UDS DIAGNOSTIC AUTOMATED TEST RUNNER")
    print("  Standards: ISO 14229 (UDS) | ISO 15765-2 (DoCAN)")
    print("=" * 65)
    
    # Run pytest programmatically with verbose output
    exit_code = pytest.main(["-v", "test_uds_diagnostics.py"])
    
    print("\n" + "=" * 65)
    if exit_code == 0:
        print("  VERIFICATION RESULT: ALL TEST CASES PASSED (100% SUCCESS)")
    else:
        print("  VERIFICATION RESULT: TEST SUITE FAILED (Check logs above)")
    print("=" * 65)

if __name__ == "__main__":
    main()