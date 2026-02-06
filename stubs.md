# Testing Strategy for TV Ratings Automation

## Philosophy

This project doesn't need unit tests. The value is in **integration points** (email → download → parse → send), not isolated functions. Testing individual methods would just test pandas and requests behavior.

Instead, we test the 4 main **modules** (pipeline stages) using stub services and scenario files.

## The 4 Testable Modules

1. **Email Retrieval** - Search Gmail, extract password + link
2. **File Download** - Download xlsx from Digi Storage
3. **Data Processing** - Parse xlsx into formatted report DataFrame
4. **Email Sending** - Send HTML report to recipients

## Approach: Stub Services + Scenario Files

### Pattern
- Each service has a **real** and **stub** implementation
- Stub implementations read from JSON scenario files in `Data/test_scenarios/`
- Config already supports switching implementations (extend to add "test" mode)

### Structure
```
services/
  email_service.py          # Real implementation
  stub_email_service.py     # Stub implementation
  download_service.py       # Real implementation  
  stub_download_service.py  # Stub implementation
  ...

Data/
  test_scenarios/
    happy_path.json         # Normal successful run
    email_not_arrived.json  # Email hasn't come yet
    corrupted_file.json     # Bad xlsx data
    extraction_error.json   # Missing password/link
    ...
  
  test_files/               # Pre-saved xlsx files for testing
    sample_ratings.xlsx
    corrupted_ratings.xlsx
```

### Benefits
- **Fast**: No network calls, runs in seconds
- **Repeatable**: Same scenario = identical results
- **Comprehensive**: Test edge cases without manufacturing them
- **Simple**: Just JSON files + basic stub classes

## Implementation Phases

### Phase 1: Stub Services
Create stub versions of:
- `StubEmailService` - returns credentials from scenario
- `StubDownloader` - copies from test_files/ instead of downloading
- `StubEmailSender` - logs instead of sending
- Add "test" config mode to `utils/config.py`

### Phase 2: Scenario Library
Create JSON scenarios for:
- Happy path (normal day)
- Email not arrived
- Invalid credentials
- Corrupted xlsx file
- Network errors
- Missing data in xlsx

### Phase 3: Test Runner
Simple `test_runner.py`:
- Loads a scenario
- Runs the pipeline with stub services
- Prints PASS/FAIL
- NOT pytest/unittest - just a script

### Phase 4: Integration
- Add scenarios when bugs found
- Run before Pi deployment
- Keep in version control

## Example Usage
```bash
# Run all scenarios
python test_runner.py

# Run specific scenario
python test_runner.py happy_path

# Test single module
python test_runner.py --module email email_not_arrived
```

## Scenario File Format (Example)
```json
{
  "name": "happy_path",
  "description": "Normal successful run",
  "email": {
    "credentials_found": true,
    "password": "123456",
    "link": "https://s.go.ro/test"
  },
  "download": {
    "success": true,
    "file": "sample_ratings.xlsx"
  },
  "expected_outcome": "success"
}
```

## Notes
- Stub services implement same interface as real services
- Scenario files are human-readable and easily edited
- Test files are real xlsx samples saved in `Data/test_files/`
- This replaces Jupyter notebook testing (faster + more scenarios)