#!/bin/bash
set -e

# Check for Docker
if ! command -v docker &> /dev/null; then
  echo "[ERROR] Docker not found! Please install Docker: https://www.docker.com/get-started"
  exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
  echo "[ERROR] Docker Compose not found! Please install Docker Compose: https://docs.docker.com/compose/"
  exit 1
fi

# Check for Make
if ! command -v make &> /dev/null; then
  echo "[ERROR] Make not found! Please install Make: https://www.gnu.org/software/make/"
  exit 1
fi

echo "[INFO] All required tools found."
echo "[INFO] Building Docker images..."
make build

echo "[SUCCESS] Bootstrap complete!"
echo "Next steps:"
echo "  1. Run 'make up' to start the dev server."
echo "  2. Visit http://localhost:9103/docs in your browser."
echo "  3. Run 'make test' to check the test suite."
echo "  4. Run 'make coverage' to see test coverage."
echo "  5. See ONBOARDING.md for more info." 