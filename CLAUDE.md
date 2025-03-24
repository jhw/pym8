# Project Guidelines

## Project Overview
- This project is a reader/writer for the Dirtywave M8 tracker binary file format
- Core functionality lives in m8/api
- Tests mirror the structure of the main codebase in the /tests directory

## Code Requirements

### Critical Rules
- **NO TYPE HINTS**: Never include Python type annotations
- **NO COMMENTS**: Do not add explanatory comments unless explicitly requested or for genuinely complex algorithms
- **NO BACKWARDS COMPATIBILITY**: Avoid "if legacy format..." logic
- **NO INLINE DEFAULTS**: Don't use patterns like `value = data.get("field", "default")`

### Code Style
- Keep functions focused on a single responsibility
- Use descriptive variable names that match domain terminology
- Follow existing code style and conventions in the project
- When working with files, check if corresponding tests exist and update them
- Assume input data is valid - don't defensively check inputs
- When using YAML, always use `yaml.dump()` with `default_flow_style=False` and `sort_keys=True` to maintain consistent formatting and predictable field order

## Utility Tools
- Use tools in the `tools/` directory for common operations
- For string pattern substitution across multiple files, use `tools/string_substitution.py`
  - This is helpful for refactoring enum strings, renaming identifiers, etc.
  - See `tools/fix_case.py` for an example of how to use it
- For general code refactoring that requires complex pattern matching, always use these tools rather than manual edits

## Testing Workflow
1. All tests live in the /tests directory mirroring the m8 directory structure
2. For changes to m8/api/foo.py, look for corresponding tests in tests/api/foo.py
3. Run tests with `python run_tests.py` after making any changes
4. Create/update tests when adding new functionality
5. If you go through more than 3 test cycles with worsening error percentages, stop and ask for help

## Task Management
- Check TODO.md for prioritized tasks
- When completing a task, move it from its section to the "done" section in TODO.md

## Git Workflow
- Always work in branch `claude-code`
- Stage files incrementally in logical groups for substantial changes
- Always test before staging
- Always ask before committing
- Don't push anything to origin
- Don't create tags unless specifically asked

## Environment
- Dependencies are listed in requirements.txt
- Pip-installed dependencies live in env/lib/python3.10/site-packages