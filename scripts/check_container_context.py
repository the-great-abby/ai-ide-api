#!/usr/bin/env python3
import os
import sys

# Check for Docker environment by env var or marker file
IN_DOCKER = (
    os.environ.get("RUNNING_IN_DOCKER") == "1"
    or os.path.exists("/.dockerenv")
    or os.path.exists("/app/.dockerenv")
)

if not IN_DOCKER:
    sys.stderr.write(
        "\n[ERROR] This command must be run inside the correct Docker container.\n"
    )
    sys.stderr.write(
        "Either use the appropriate Makefile.ai target or run inside the documented container.\n"
    )
    sys.stderr.write("See CONTAINER_COMMANDS.md for details.\n\n")
    sys.exit(1)

# If imported, this will just run the check on import
