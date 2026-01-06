from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the repository root is on sys.path so `import sdet_agent` works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Also ensure PYTHONPATH includes repo root for subprocess invocations
os.environ.setdefault("PYTHONPATH", str(ROOT))
