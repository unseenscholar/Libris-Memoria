# markdown-book-parser

**Purpose:** Migrate old Markdown library files to `libris-memoria.toml` format,
and generate series progress reports from the TOML.

## Usage
```bash
python generate_report.py migrate old_library.md
python generate_report.py report
python generate_report.py report --json
```

## Migration Notes
- Star ratings (★★★★) are converted to `/10` scale (each ★ = 2 pts, ½ = 1 pt)
- Genre codes are left as `[]  # TODO` — fill in after migration
- Series keys are auto-generated short slugs — rename if needed
- Review the output before appending to your TOML file

## Dependencies
- `lm_core.py` (shared TOML loader, one directory up)
