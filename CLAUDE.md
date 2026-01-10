# Claude Code Guidelines for pym8

## Project Preferences

### No Backwards Compatibility / Legacy Code
- Do not add backwards compatibility shims or legacy code patterns
- When refactoring, remove old code completely rather than keeping deprecated versions
- Do not add `# deprecated` comments - just delete unused code
- No re-exports of moved modules for compatibility
- No `_old` or `_legacy` suffixed functions/variables

### Code Style
- Keep solutions simple and focused
- Avoid over-engineering - only implement what's directly needed
- No speculative features or "future-proofing"
- Delete unused code rather than commenting it out

### Testing
- Tests live in `tests/` mirroring the `m8/` structure
- Use `unittest` (not pytest)
- Run tests with: `python run_tests.py`

### Project Structure
- Core library: `m8/api/`
- Instrument types: `m8/api/instruments/`
- Audio tools: `m8/tools/`
- Demo scripts: `demos/`
- Project management scripts: `tools/`

### M8 File Format
- Binary format with fixed offsets
- Little-endian byte order
- Reference: [m8-file-parser](https://github.com/Twinside/m8-file-parser) (Rust)
- Target firmware: 6.2+
