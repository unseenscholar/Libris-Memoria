# Series Report Generator Skill

## Purpose
Generate comprehensive reports on all completed book series with detailed progress tracking, completion percentages, and reading insights.

## Features
- ✅ Lists all read/completed series
- ✅ Shows completion percentage for each series
- ✅ Displays books remaining to complete
- ✅ Suggests next book in partial series
- ✅ Tracks reading order across the series
- ✅ Provides helpful progress notes
- ✅ Exports to JSON format for further analysis

## How to Use

### Quick Command
```bash
cd /root/.picoclaw/workspace/skills/markdown-book-parser
./generate_series_report.sh [library_file]
```

Example:
```bash
./generate_series_report.sh my-library.md
```

### Python Script (Advanced)
```python
from markdown_book_parser import parse_library_file
from markdown_book_parser.generate_report import generate_series_report, main

# Parse your library
library_data = parse_library_file("library.md")

# Generate report
report = generate_series_report(library_data)

# Access data
for series in report["series"]:
    print(f"{series['name']}: {series['completion_percentage']} complete")
```

## Output Format
Generates `series_report.json` with:
- Total completed series count
- Standalone books not in any series
- Detailed progress for each series:
  - Name and completion percentage
  - Books read vs total in series
  - Next suggested book (if incomplete)
  - Average rating (if available)
  - Reading order across the series

## Example Output
```
📚 Generating Book Series Report...
Library file: library.md

✅ Report generated: series_report.json
   Found 5 completed series

--- Completed Series Summary ---
Harry Potter: 4/7 (57.1%) - Next up: Harry Potter and the Order of the Phoenix (Book 5)
The Lord of the Rings: 3/6 (50.0%) - Almost done! Just 2 book(s) left to finish.
...
```

---
*Skill ready for use...*
