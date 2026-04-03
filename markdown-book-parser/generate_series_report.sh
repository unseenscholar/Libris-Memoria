#!/bin/bash
# Generate Book Series Report
# Usage: ./generate_series_report.sh [library_file]

LIBRARY_FILE="${1:-library.md}"

echo "📚 Generating Book Series Report..."
echo "Library file: $LIBRARY_FILE"
echo ""

cd /root/.picoclaw/workspace/skills/markdown-book-parser

# Check if Python script exists
if [ ! -f "generate_report.py" ]; then
    echo "❌ Error: generate_report.py not found. Please run this skill first."
    exit 1
fi

# Parse library and generate report
python3 generate_report.py "$LIBRARY_FILE"

echo ""
echo "📊 Report saved to: /root/.picoclaw/workspace/skills/markdown-book-parser/series_report.json"
echo ""
echo "Quick Summary:"
if [ -f "series_report.json" ]; then
    python3 -c "import json; data=json.load(open('series_report.json')); print(f'   • {data[\"total_read_series\"]} completed series'); print(f'   • {data.get(\"total_standalone_books\", 0)} standalone books')"
fi
