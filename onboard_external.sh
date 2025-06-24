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

# Pirate Buddy System
BUDDIES=("Patch McDebug" "Captain Abby" "Doc Testwell" "Dave the Database Deckhand" "Maple Cartwright" "Bosun Riggs" "Random")
declare -A BUDDY_INTROS
BUDDY_INTROS["Patch McDebug"]="Arrr, I be Patch McDebug, yer relentless bug-hunter! Let's get ye shipshape."
BUDDY_INTROS["Captain Abby"]="Welcome aboard! Captain Abby here to chart your course to greatness."
BUDDY_INTROS["Doc Testwell"]="Ahoy! Doc Testwell at your service—let's keep things healthy and well-tested."
BUDDY_INTROS["Dave the Database Deckhand"]="Dave here! I'll help you wrangle the data seas."
BUDDY_INTROS["Maple Cartwright"]="Maple Cartwright, navigator extraordinaire—let's find your way."
BUDDY_INTROS["Bosun Riggs"]="Bosun Riggs reporting! Automation and efficiency be my game."
ENCOURAGEMENTS=(
  "Well done, matey!"
  "Onward to the next step!"
  "If ye get stuck, don't hesitate to ask for help."
)

# Buddy selection
printf "\nChoose yer buddy for this voyage:\n"
for i in "${!BUDDIES[@]}"; do
  printf "%d) %s\n" $((i+1)) "${BUDDIES[$i]}"
done
read -p "> " BUDDY_INDEX
BUDDY_INDEX=$((BUDDY_INDEX-1))
SELECTED_BUDDY="${BUDDIES[$BUDDY_INDEX]}"
if [ "$SELECTED_BUDDY" == "Random" ]; then
  SELECTED_BUDDY="${BUDDIES[$((RANDOM % (${#BUDDIES[@]}-1)))]}"
fi
printf "\n%s\n\n" "${BUDDY_INTROS[$SELECTED_BUDDY]}"

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