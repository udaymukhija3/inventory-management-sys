#!/usr/bin/env python3
"""
Compatibility wrapper for the supported SQL-based demo seed.

The original API seeding flow relied on endpoints that do not create the full
inventory dataset cleanly. The supported path is deterministic SQL seeding via
scripts/seed-data.sh.
"""

import subprocess
import sys


def main() -> int:
    print("The supported demo dataset is loaded via scripts/seed-data.sh")
    return subprocess.call(["bash", "scripts/seed-data.sh"])


if __name__ == "__main__":
    sys.exit(main())
