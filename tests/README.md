# Tests for BetterHTMLChunking

This directory contains the test suite for the BetterHTMLChunking library.

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_main.py -v
```

### Run specific test class
```bash
pytest tests/test_main.py::TestDomRepresentation -v
```

### Run specific test
```bash
pytest tests/test_main.py::TestDomRepresentation::test_basic_initialization -v
```

### Run with coverage (requires pytest-cov)
```bash
pip install pytest-cov
pytest tests/ --cov=betterhtmlchunking --cov-report=html
```

## Test Structure

- `test_main.py` - Tests for the main API (DomRepresentation)
- `test_tree_representation.py` - Tests for DOM tree representation
- `test_tree_regions_system.py` - Tests for ROI detection system
- `test_utils.py` - Tests for utility functions
- `test_cli.py` - Tests for command-line interface functionality

## Test Coverage

The test suite covers:
- Basic HTML parsing and tree construction
- Region of Interest (ROI) detection
- Different comparison modes (text length vs HTML length)
- Tag filtering functionality
- Edge cases (empty HTML, malformed HTML, deeply nested structures)
- API integration and full processing pipeline
- CLI functionality:
  - Basic command-line operations
  - `--list-chunks` for listing chunk information
  - `--all-chunks` for saving all chunks to files
  - `--text-only` for plain text output
  - `--format json` for structured JSON output
  - Verbosity levels and logging
  - Integration between CLI features
