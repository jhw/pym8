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
- Always stage changes first, allowing manual review before commit
- Wait for confirmation of successful testing before committing
- When suggesting changes that affect multiple files, summarize the changes
- DO NOT create any tags without asking first
- When asked to create a tag, lookup the list of tags and bump the minor version, then push to origin

## Testing

- DO NOT run any tests, I will do it manually

