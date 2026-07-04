# 📊 Excel Agent Guide — AI Rules for Excel Document Handling

## Objective
This document defines mandatory protocols for AI agents when creating, modifying, or debugging Excel workbooks (`.xlsx`, `.xlsm`) in this repository. It captures all hard-won lessons from real-world Mac/Windows Excel compatibility debugging to prevent repeated mistakes.

---

## 1. Core Principles

### 1.1 Pre-Compute, Don't Formula-Embed
**CRITICAL:** AI agents MUST pre-compute all derived values in Python and write them as **static values** into Excel cells. NEVER embed Excel formulas (e.g., `=DATEVALUE(...)`, `=WEEKNUM(...)`, `=VLOOKUP(...)`) unless the user explicitly requests live formulas.

**Why:**
- Mac Excel is extremely picky about formula compatibility inside Excel Tables
- Version-specific functions (`ISOWEEKNUM`, `XLOOKUP`, `LAMBDA`) may not exist on all Excel versions
- Formulas cascading from text fields (ISO timestamps) cause `#VALUE!` chains
- Pre-computed values **guarantee** the workbook opens cleanly on all platforms

| 🟢 **Good** | 🔴 **Bad** |
|-------------|-----------|
| `ws["K2"] = date_obj.strftime("%Y-%m-%d")` | `ws["K2"] = '=DATEVALUE(LEFT(B2,10))'` |
| `ws["L2"] = int(hour)` | `ws["L2"] = '=VALUE(MID(B2,12,2))'` |
| `ws["O2"] = date_obj.isocalendar()[1]` | `ws["O2"] = '=ISOWEEKNUM(DATEVALUE(LEFT(B2,10)))'` |

### 1.2 NEVER Use openpyxl Excel Tables
**CRITICAL:** AI agents MUST NEVER create Excel Tables (`ws.add_table()`) via openpyxl. Use plain formatted ranges with auto-filter instead.

**Why:**
- openpyxl's Excel Table XML implementation triggers **file-format validation errors** on Mac Excel
- Even tables with zero formulas fail on Mac when they exceed a certain row count or column complexity
- The error message is generic: *"Excel cannot open the file because the file format or file extension is not valid"*

| 🟢 **Good** | 🔴 **Bad** |
|-------------|-----------|
| `ws.auto_filter.ref = f"A1:Q{last_row}"` | `ws.add_table(tab)` / `tab = Table(...)` |

### 1.3 Always Add Defensive Row Guards
**MANDATORY:** Every loop that reads data rows destined for Excel MUST validate each field before access. Use `.get()` with None/empty/type checks. Never assume `row["key"]` exists.

**Why:** CSVs and database exports routinely contain bad rows (empty model names, null costs, malformed dates). Without guards, the build crashes with `KeyError` or `ValueError`.

```python
# 🟢 GOOD: Defensive validation before every field access
for idx, row in enumerate(rows, 1):
    hour_bucket = row.get("hour_bucket")
    if not hour_bucket or not isinstance(hour_bucket, str):
        print(f"⚠ Skipping row {idx}: missing or invalid hour_bucket")
        continue
    model = row.get("model")
    if not model or not isinstance(model, str) or model.strip() == "":
        print(f"⚠ Skipping row {idx}: missing or invalid model")
        continue
    # ... safe to use validated fields now ...
```

```python
# 🔴 BAD: Blind key access — crashes on missing fields
cost = float(row["cost"])       # KeyError if 'cost' is missing
model = row["model"]            # NoneType if model is null
hour = dt.strptime(hour_bucket) # ValueError if empty string
```

### 1.4 Formula Cache Preservation on Write-Back (openpyxl)

**Background:** openpyxl has no formula evaluation engine. When `wb.save()` is called, it strips all cached computed values (`<v>` elements) from formula cells. After save, `data_only=True` reads (used by `excel_query_sql`, `excel_scan_for_errors`, and `pandas`) return `None`/`NaN` for those cells — silently corrupting downstream AI analysis.

**Solution #4:** All write-capable Excel tools now use `safe_save()` (from `backend/core/excel_tools/formula_cache.py`) instead of `wb.save()`. This function:
1. Captures all cached computed values from the original file (via `data_only=True`)
2. Monkey-patches openpyxl's cell writers to inject those cached values into `<v>` elements after `<f>` elements
3. Saves the workbook with cached values preserved
4. Restores original writers in a `finally` block

**Impact on AI agents:** Every write tool response now includes `formulas_preserved` (count) and `formulas_stale_warning` (always `true` — the AI must warn users that edits may have invalidated formula dependencies). Read tools (`excel_query_sql`, `excel_scan_for_errors`) now see correct computed values after write-back instead of `NaN`/`None`.

### 1.5 Sequential Write-Row Counter
When skipping bad rows, use a **separate write-row counter** (not `enumerate` index) so valid rows are written consecutively with no empty gaps in the sheet.

```python
# 🟢 GOOD: Separate write pointer
write_row = 2
for idx, row in enumerate(rows, 1):
    if not valid: continue
    ws.cell(row=write_row, column=1, value=...)
    write_row += 1
```

```python
# 🔴 BAD: enumerate index leaves gaps
for idx, row in enumerate(rows, 1):
    if not valid: continue
    ws.cell(row=idx + 1, column=1, value=...)  # gap at idx+1!
```

---

## 2. Version-Specific Function Blacklist

The following Excel functions are **BANNED** from AI-generated formulas unless the user explicitly confirms their Excel version supports them:

| Banned Function | Safe Replacement | Why |
|-----------------|------------------|-----|
| `ISOWEEKNUM()` | Pre-compute in Python with `datetime.isocalendar()[1]` | Not available on Mac Excel pre-2016 |
| `XLOOKUP()` | Pre-compute in Python | Office 365+ only |
| `LAMBDA()` | Pre-compute in Python | Office 365+ only |
| `TEXTJOIN()` | Pre-compute in Python | Excel 2019+ only |
| `FILTER()` | Pre-compute in Python | Office 365+ only |

**Rule:** If the value can be computed in Python before writing, **always pre-compute it**.

---

## 3. Workbook Verification Protocol

After building or modifying an Excel file, AI agents MUST run these verification steps:

### 3.1 Manifest Check
```python
excel_get_manifest(path="token_usage.xlsx")
# Verify: correct sheet count, sheet names, no hidden corruption
```

### 3.2 Data Integrity Check
```python
excel_read_range(path="token_usage.xlsx", sheet_name="Data", range_address="K2:Q5")
# Verify: no formulas, no #VALUE!, no #NAME?, no None cells
```

### 3.3 Chart Verification
```python
excel_list_charts(path="token_usage.xlsx")
# Verify: expected chart count present
```

### 3.4 Formula Sweep (if formulas are intentional)
```python
excel_scan_for_errors(path="token_usage.xlsx", sheet_name="Data")
# Verify: zero formula errors
```

### 3.5 Git Diff Self-Review
```python
get_current_diff()
# Verify: no accidental deletions, no placeholder comments, no broken paths
```

---

## 4. Credential Security

### 4.1 NEVER Hardcode Secrets
AI agents MUST NEVER embed API keys, JWT tokens, or database passwords as string literals in any file (Python, VBA, or documentation).

| 🟢 **Good** | 🔴 **Bad** |
|-------------|-----------|
| `key = _load_env_var("ANON_KEY")` | `ANON_KEY = "eyJhbGciOi..."` |
| `key = open(".anon_key.dat").read().strip()` | Hardcoded 170-char JWT in source |
| Reference: "found in `.env`" | Reference: "the key is: eyJ..." |

### 4.2 VBA Key Loading
VBA modules MUST load credentials at runtime from:
- **Option A:** Hidden `_Config` sheet in the workbook
- **Option B:** `.anon_key.dat` file next to the workbook

Never embed the key as a VBA constant.

---

## 5. Port & URL Configuration

### 5.1 Always Auto-Detect Ports
AI agents MUST read `KONG_HTTP_PORT` from `supabase-docker/.env` instead of hardcoding port numbers in scripts or VBA.

**Why:** The `.env` maps `KONG_HTTP_PORT=8015` to internal `8000`. Using `SUPABASE_PUBLIC_URL` (which says `8025`) will always fail — port `8025` was never mapped.

```python
# 🟢 GOOD: Auto-detect from .env
kong_port = _load_env_var("KONG_HTTP_PORT", default="8015")
url = f"http://localhost:{kong_port}/rest/v1/token_usage_hourly"
```

```python
# 🔴 BAD: Hardcoded from SUPABASE_PUBLIC_URL
url = "http://localhost:8025/rest/v1/token_usage_hourly"  # always fails
```

---

## 6. Mac Excel Compatibility

### 6.1 VBA Editor Access
Mac Excel uses different shortcuts:

| Action | Mac | Windows |
|--------|-----|---------|
| **Open VBA Editor** | **Tools → Macro → Visual Basic Editor** | `Alt+F11` |
| **Keyboard shortcut** | `Fn+Option+F11` or `Option+F11` | `Alt+F11` |
| **Import file** | `Cmd+I` or File → Import File | `Ctrl+M` or File → Import File |

Always provide BOTH menu path and keyboard shortcut in instructions.

### 6.2 Mac HTTP in VBA
Mac Excel VBA does NOT support `WinHttp.WinHttpRequest.5.1`. Provide:
- **MSXML2** as primary cross-platform HTTP client
- **Python bridge** fallback (`MacScript` / `AppleScript` → `python3 script.py`)
- Accept that sync from VBA may not work on Mac without Python fallback

### 6.3 File Extension
openpyxl produces `.xlsx`-format ZIP structure regardless of filename. Save as `.xlsx` (not `.xlsm`). VBA modules are imported manually by the user, who then saves-as `.xlsm`.

---

## 7. Dashboard Design Standards

### 7.1 Zero-VBA Baseline
All dashboards MUST be **immediately useful without VBA**:
- Real computed values, not placeholders
- Native Excel charts rendered via openpyxl
- Summary tables with pre-computed aggregations

VBA (Pivot Tables, Slicers) is an **upgrade path**, not a requirement for first-open usability.

### 7.2 Dashboard Sections
Standard dashboard layout for analytics workbooks:
1. **Info Bar** (Row 2): Date range, row count, model count, build timestamp
2. **KPI Cards** (Row 4-5): 4 top-level metrics with large bold values
3. **Summary Tables + Charts** (Rows 7+): Paired table+chart sections side-by-side
4. **VBA Upgrade Note** (Bottom): Instructions for interactive slicer upgrade

### 7.3 Chart Types
| Data Relationship | Chart Type |
|-------------------|------------|
| Ranking (e.g., cost by model) | **Bar Chart** (vertical or horizontal) |
| Time series (e.g., weekly tokens) | **Line Chart** |
| Proportional (e.g., token share) | **Pie Chart** |
| Efficiency comparison | **Horizontal Bar Chart** |
| Matrix/Grid (e.g., hour × model) | **Color-scale conditional formatting** |

---

## 8. Progressive Reporting

When building Excel workbooks across multiple phases, AI agents MUST use `report_progress` to keep the user informed:

```python
report_progress(status="Phase 1/4", details="Extracting data from Supabase...")
# ... extract ...
report_progress(status="Phase 2/4", details="Building workbook foundation...")
# ... build ...
report_progress(status="Phase 3/4", details="Creating dashboard and charts...")
# ... dashboard ...
report_progress(status="Phase 4/4", details="Applying styling and verification...")
```

---

## 9. Diagnostic Protocol for Opening Errors

When a user reports that Excel cannot open a file, follow this protocol:

1. **Verify ZIP integrity:** The `.xlsx` is a ZIP. Check it opens.
2. **Check for Excel Tables:** `excel_list_tables()` — remove all tables if present
3. **Check for formulas:** `excel_read_range()` on computed columns — replace with pre-computed values
4. **Isolate the culprit:** Create minimal diagnostic files (single worksheet, 10 rows) adding features one at a time:
   - Plain data only → test
   - + Formatting → test
   - + Auto-filter → test
   - NEVER add Excel Tables
5. **Fallback:** If all else fails, write pure static values with zero formatting and rebuild incrementally

---

## 10. File Inventory During Excel Projects

Expected file layout for an Excel analytics project:

```
project-root/
├── token_usage.xlsx              # Primary deliverable (formula-free, table-free)
├── scripts/
│   ├── build_excel_workbook.py   # Builds .xlsx from CSV/SQL source
│   └── sync_token_usage.py       # Fetches fresh data (stdlib only, no pip deps)
├── vba/
│   ├── modJsonParser.bas         # JSON parser (import first!)
│   ├── modSupabaseSync.bas       # HTTP sync engine
│   ├── modDashboardBuilder.bas   # Pivot Tables + Charts + Slicers generator
│   ├── modUtilities.bas          # Progress bar, logging helpers
│   └── ThisWorkbook.cls          # Workbook_Open auto-build handler
├── docs/
│   └── token_usage_excel.md      # Design document with implementation checklist
├── .anon_key.dat                 # (Optional) ANON_KEY for Option B VBA loading
└── rules/
    └── Excel_Agent_Guide.md      # This file
```

---

## 11. Summary Checklist for AI Agents

Before finalizing ANY Excel-related task, verify:

- [ ] **No Excel Tables** — `excel_list_tables()` returns `[]`
- [ ] **No formulas in Data sheet** — all values pre-computed in Python
- [ ] **No version-specific functions** — no `ISOWEEKNUM`, `XLOOKUP`, `LAMBDA`
- [ ] **Defensive row guards** — every field validated before access
- [ ] **Sequential write-row counter** — no gaps from skipped rows
- [ ] **No hardcoded credentials** — grep for `eyJh` returns zero matches
- [ ] **Ports auto-detected** — reads from `.env`, not hardcoded
- [ ] **Dashboard renders without VBA** — real data and charts on first open
- [ ] **Mac instructions provided** — Tools → Macro → Visual Basic Editor path
- [ ] **`report_progress` used** — multi-phase builds report progress
- [ ] **`get_current_diff` reviewed** — no accidental deletions or placeholders
- [ ] **`check_syntax` passed** — zero errors on all modified files
