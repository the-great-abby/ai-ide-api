#!/bin/bash

# Patch's PathFinder: Interactive Onboarding Script
# Note: API integration coming soon! For now, steps are loaded from onboarding_paths.json.

ONBOARDING_PATHS_FILE="onboarding_paths.json"

# Sample buddy personalities
declare -A BUDDY_INTROS
BUDDY_INTROS=(
  ["Patch McDebug"]="Arrr, I be Patch McDebug, yer relentless bug-hunter! Let's get ye shipshape."
  ["Captain Abby"]="Welcome aboard! Captain Abby here to chart your course to greatness."
  ["Doc Testwell"]="Ahoy! Doc Testwell at your service—let's keep things healthy and well-tested."
  ["Dave the Database Deckhand"]="Dave here! I'll help you wrangle the data seas."
  ["Maple Cartwright"]="Maple Cartwright, navigator extraordinaire—let's find your way."
  ["Bosun Riggs"]="Bosun Riggs reporting! Automation and efficiency be my game."
)

BUDDIES=("Patch McDebug" "Captain Abby" "Doc Testwell" "Dave the Database Deckhand" "Maple Cartwright" "Bosun Riggs" "Random")

# Load onboarding paths from JSON
if ! [ -f "$ONBOARDING_PATHS_FILE" ]; then
  echo "Error: $ONBOARDING_PATHS_FILE not found. Please add onboarding_paths.json."
  exit 1
fi

# List available paths
echo "Ahoy! Welcome to Patch's PathFinder."
echo "Which onboarding path do ye seek?"
PATHS=($(jq -r '.paths[].name' "$ONBOARDING_PATHS_FILE"))
for i in "${!PATHS[@]}"; do
  printf "%d) %s\n" $((i+1)) "${PATHS[$i]}"
done
read -p "> " PATH_INDEX
PATH_INDEX=$((PATH_INDEX-1))
SELECTED_PATH="${PATHS[$PATH_INDEX]}"

# Choose a buddy
echo "\nChoose yer buddy for this voyage:"
for i in "${!BUDDIES[@]}"; do
  printf "%d) %s\n" $((i+1)) "${BUDDIES[$i]}"
done
read -p "> " BUDDY_INDEX
BUDDY_INDEX=$((BUDDY_INDEX-1))
SELECTED_BUDDY="${BUDDIES[$BUDDY_INDEX]}"
if [ "$SELECTED_BUDDY" == "Random" ]; then
  SELECTED_BUDDY="${BUDDIES[$((RANDOM % (${#BUDDIES[@]}-1)))]}"
fi

# Buddy intro
echo -e "\n${BUDDY_INTROS["$SELECTED_BUDDY"]}\n"

# Fetch steps for the selected path
STEPS_LEN=$(jq ".paths[] | select(.name==\"$SELECTED_PATH\") | .steps | length" "$ONBOARDING_PATHS_FILE")
for ((i=0; i<$STEPS_LEN; i++)); do
  STEP=$(jq -r ".paths[] | select(.name==\"$SELECTED_PATH\") | .steps[$i].instruction" "$ONBOARDING_PATHS_FILE")
  DOC_LINK=$(jq -r ".paths[] | select(.name==\"$SELECTED_PATH\") | .steps[$i].doc_link // empty" "$ONBOARDING_PATHS_FILE")
  echo -e "Step $((i+1)): $STEP"
  if [ -n "$DOC_LINK" ]; then
    echo "(Docs: $DOC_LINK)"
  fi
  read -p "[Press Enter when done, or type 'help' for more info] " REPLY
  if [ "$REPLY" == "help" ] && [ -n "$DOC_LINK" ]; then
    open "$DOC_LINK"
  fi
  # Sample buddy encouragement
  case $((RANDOM % 3)) in
    0) echo "$SELECTED_BUDDY: Well done, matey!";;
    1) echo "$SELECTED_BUDDY: Onward to the next step!";;
    2) echo "$SELECTED_BUDDY: If ye get stuck, don't hesitate to ask for help.";;
  esac
  echo

done

echo "$SELECTED_BUDDY: Congratulations! Ye completed the $SELECTED_PATH onboarding path. Fair winds!" 