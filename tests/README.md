# Tests

This directory contains all test files for the MCP_Gesetze project.

## Running Tests

From the project root:

```bash
# Parser tests
python tests/test_parser.py

# Forward reference tests
python tests/test_forward_refs.py

# MCP server functional tests
python tests/test_mcp_server.py

# MCP server caching tests
python tests/test_mcp_cache.py

# Type checking
mypy src/*.py tests/*.py mcp_server.py
```

## Test Files

### Parser Tests
- **test_parser.py**: Tests the XML parser with example law files
- **test_forward_refs.py**: Tests Pydantic model forward references

### MCP Server Tests
- **test_mcp_server.py**: Functional tests for all MCP server tools
- **test_mcp_cache.py**: Performance tests for lazy loading and caching
