#!/bin/bash
# External Onboarding Script for AI-IDE-API
# Wrapper script for the Python onboarding process

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🏴‍☠️  AI-IDE-API External Onboarding${NC}"
echo "=========================================="
echo "This script will help you set up external access to the AI-IDE-API."
echo ""

# Check if Python script exists
ONBOARDING_SCRIPT="$SCRIPT_DIR/onboard_external_updated.py"
if [ ! -f "$ONBOARDING_SCRIPT" ]; then
    echo -e "${RED}❌ Onboarding script not found: $ONBOARDING_SCRIPT${NC}"
    exit 1
fi

# Check if makefile generator exists
MAKEFILE_GENERATOR="$SCRIPT_DIR/generate_external_makefile.py"
if [ ! -f "$MAKEFILE_GENERATOR" ]; then
    echo -e "${RED}❌ Makefile generator not found: $MAKEFILE_GENERATOR${NC}"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Run the onboarding script
echo -e "${GREEN}🚀 Starting external onboarding...${NC}"
echo ""

python3 "$ONBOARDING_SCRIPT" "$@"

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 External onboarding completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Review the generated files:"
    echo "   - Makefile.external"
    echo "   - README.external.md"
    echo "   - example_memory.txt"
    echo "   - example_rule.mdc"
    echo ""
    echo "2. Start using the API:"
    echo "   make -f Makefile.external help"
    echo ""
    echo -e "${GREEN}🏴‍☠️  Happy coding with AI-IDE-API!${NC}"
else
    echo ""
    echo -e "${RED}❌ External onboarding failed${NC}"
    echo "Please check the errors above and try again."
    exit 1
fi 