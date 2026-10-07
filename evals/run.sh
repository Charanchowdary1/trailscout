#!/bin/bash
# Runs the TrialScout eval from this folder, then opens the results grid.
cd "$(dirname "$0")" || exit 1

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is not installed. Install the LTS version from nodejs.org, open a new Terminal, and try again."
  exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ANTHROPIC_API_KEY is not set in this Terminal window."
  echo "Type this first (with your own key):  export ANTHROPIC_API_KEY=your-key"
  exit 1
fi

for f in promptfooconfig.yaml tests.yaml prompts/v3_explain_terms.txt prompts/v4_final.txt prompts/v5_example.txt; do
  if [ ! -f "$f" ]; then
    echo "Missing file: $f  (re-extract the zip into a fresh folder)"
    exit 1
  fi
done

npx promptfoo@latest eval && npx promptfoo@latest view
