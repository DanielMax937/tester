from __future__ import annotations

import subprocess
import sys


def main() -> int:
    result = subprocess.run(
        ["docker", "run", "--rm", "test-target"],
        capture_output=True,
        text=True,
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr, file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    if "hello" not in result.stdout.lower():
        raise SystemExit("Expected output to contain 'hello'")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
