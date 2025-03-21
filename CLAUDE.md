# Project Preferences

## Project Structure

- This project is a reader/writer for the Dirtywave M8 tracker binary file format
- Core functionality lives in m8/api

## Environment

- see requirements.txt
- pip- installed dependencies live in env/lib/python3.10/site-packages

## Code Style

- DO NOT create backwards compatible code (no "if legacy format..." logic)
- DO NOT create inline defaults (e.g., `value = data.get("field", "default")`) - assume data is valid
- Add explanatory comments only for complex algorithms, non-obvious design decisions, and important implementation details that would aid future maintenance and refactoring
- Use descriptive variable names that match the domain terminology
- Keep functions focused on a single responsibility
- Follow existing code style and conventions in the project

## Git Workflow

- Always work in branch claude-code; if this doesn't exist, create it; if you are not on this branch, check it out
- For substantial changes, stage files incrementally in logical groups
- When suggesting changes that affect multiple files, summarize the changes
- Always test before staging; ALWAYS ask before committing
- DO NOT create any tags unless asked
- When asked to create a tag, lookup the list of tags and bump the minor version, then push to origin

## Testing 

- There is an extensive test suite in /tests and a script which runs all tests called run_tests.py
- Run this to see if changes you have made pass and reflect on the results when iterating towards solutions

