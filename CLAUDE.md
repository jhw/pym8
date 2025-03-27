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

## Migration Scripts
- For architectural refactoring that involves moving code between modules, create a script in the `migrations/` directory
- Name scripts descriptively with a `move_` prefix (e.g., `migrations/move_validation_result.py`)
- Migration scripts should:
  1. Move code elements from source to destination
  2. Update all import references throughout the codebase
  3. Include validation to ensure the migration worked correctly 
  4. Print clear status messages for each step
- Run tests after executing migration scripts to verify functionality

## Testing Workflow
1. All tests live in the /tests directory mirroring the m8 directory structure
2. For changes to m8/api/foo.py, look for corresponding tests in tests/api/foo.py
3. Run tests with `python run_tests.py` after making any changes
4. Create/update tests when adding new functionality
5. If you go through more than 3 test cycles with worsening error percentages, stop and ask for help

## Task Management
- Check TODO.md for prioritized tasks
- When completing a task, move it from its section to the "done" section in TODO.md

## Notes Management
- When adding new notes to NOTES.md, always add them at the top of the file
- Include the current date in dd/mm/yyyy format in parentheses in the section header
- Example: `## New Feature Implementation (26/03/2025)`

## Git Workflow
- Stage files incrementally in logical groups for substantial changes
- Always test before staging
- Always ask before committing
- Don't push anything to origin
- Don't create tags unless specifically asked
- **IMPORTANT**: Always commit changes before requesting a conversation compaction
  - This ensures work isn't lost when the context is reset
  - Helps maintain accurate commit messages that reflect all related changes
  - Creates clear breakpoints between logical tasks

## Environment
- Dependencies are listed in requirements.txt
- Pip-installed dependencies live in env/lib/python3.10/site-packages
