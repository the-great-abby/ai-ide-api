import os
import sys

ok = True

print("[healthcheck] Starting misc-scripts healthcheck...")

# Check Python
try:
    import platform
    print(f"[OK] Python version: {platform.python_version()}")
except Exception as e:
    print(f"[ERROR] Python not available: {e}")
    ok = False

# Check /scripts directory
if os.path.isdir("/scripts"):
    print("[OK] /scripts directory exists")
else:
    print("[ERROR] /scripts directory missing")
    ok = False

# Check for at least one known script
if os.path.exists("/scripts/memory_utils.py"):
    print("[OK] memory_utils.py found in /scripts")
else:
    print("[ERROR] memory_utils.py not found in /scripts")
    ok = False

if ok:
    print("[PASS] misc-scripts healthcheck passed!")
    sys.exit(0)
else:
    print("[FAIL] misc-scripts healthcheck failed!")
    sys.exit(1) 