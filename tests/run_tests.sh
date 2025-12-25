#!/bin/sh
# Full Pipeline Runner
# Usage: ./run_tests.sh

# 1. Create output directories if they don't exist
mkdir -p cst ast errors

echo "Starting Build Pipeline..."
echo "--------------------------------"

# 2. Loop through all .clean source files in the 'tests' folder
for f in tests/*.clean; do
  # Check if files exist to avoid errors on empty folders
  [ -e "$f" ] || continue 
  
  name=$(basename "$f" .clean)
  echo "Processing: $name"

  # STEP 1: PARSE (Source -> CST)
  # Changed python3 -> python
  if python parser.py "$f" > "cst/$name.json"; then
      echo "  [✓] Parser: CST generated"
  else
      echo "  [X] Parser: Failed"
      continue
  fi

  # STEP 2: CONVERT (CST -> AST)
  # Changed python3 -> python
  if python converter.py "cst/$name.json" "ast/$name.json"; then
      echo "  [✓] Converter: AST generated"
  else
      echo "  [X] Converter: Failed"
      continue
  fi

  # STEP 3: ANALYZE (AST -> Semantic Errors)
  # Changed python3 -> python
  python analyzer.py "ast/$name.json" "errors/$name.err.json"
  echo "  [✓] Analyzer: Check complete (See errors/$name.err.json)"
  echo ""
done

echo "--------------------------------"
echo "Pipeline Finished."
