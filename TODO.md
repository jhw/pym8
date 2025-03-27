# short

- FMsynth inspection

# medium

- Sampler slices
- Hypersynth
- Tables

- TODO.md >> github project

- 5.0.2

# beats

- Revoke chains model in favour of phrases only
- Check reverb_send, chorus_send refs

# roadmap

- Eq
- Midi
- Grooves
- Scales

# done

- Move M8EnumValueError to core/enums.py to fix circular imports
- Improved project validation with M8ValidationResult class for better error reporting
- Added project-level validation system with unified validate() method
- Added is_complete() methods to FX and Phrase classes
- Investigate inspect_chains.py context manager warnings
- Improved phrase emptiness check to consider non-empty FX
- Updated JSON serialization for phrases to use sparse representation
- Move enums to m8/core, utils to m8/utils
- Added test for FX values using GENBASS.m8s
- Modified inspect_xxx scripts to output integers as hex values in YAML
- Fixed context manager FX key serialization issue in inspect_chains.py
- Improved M8Block type detection for getting instrument types
- Added robust fallback mechanisms for FX key serialization
- Updated code with improved debug logging that can be enabled with env var
- Enhanced context propagation to handle phrases referenced by chains
- Sort notes
- Speech input support for Claude
✓ Rename concat_phrases.py to inspect_phrases.py
✓ Abstract ID-to-string conversion boilerplate code into utility functions in enum helpers
✓ Create helper methods for common enum conversion patterns
✓ Implement ID-based approach for context manager (see "Context Manager ID-Based Implementation" in NOTES.md)
✓ Fix context manager issues with enum serialization (see "Context Manager Issues" in NOTES.md)
✓ Fix modulator destination enum serialization (see NOTES.md for details)
✓ Fix non_zero_destination_mods in example tests
✓ Enhance M8Modulator.is_empty() to consider OFF destination as empty
✓ refactor tools/concat_phrases.py and tools/bake_chains.py to use a class-based approach
✓ update tests for refactored tools
✓ phrase note enum support (M8PhraseStep with EnumPropertyMixin)
✓ phrase and fx is_empty() implementation
✓ replace concat_phrases with m8/tools version
✓ optimize enum class loading to cache loaded classes and avoid repeated loading
✓ improve error handling for invalid enum values across instruments, modulators, and fx
✓ streamline get_enum_paths_for_instrument to handle IntEnum values without redundancy
✓ add clone method to M8FXTuple to properly handle instrument_type
✓ add missing clone methods to M8ChainStep and M8Project
✓ add constructor enum support to fx
✓ add fx enums
- standardize instrument/modulator enum strings to use uppercase consistently
✓ fix docstring comments violating policy
✓ nest instrument subclasses in format yaml
✓ yaml format with hex codes
✓ implement UINT4_2 field type for packed 4-bit values in config
✓ convert common_offsets, common_defaults into field-like structure
✓ add default: 0 as third default for YAML fields
✓ default size/type defaults for YAML fields (size: 1, type: "UINT8")
✓ abstract bit utils, json utils
✓ implement proper modulator is_empty() definition using configuration
✓ implement proper is_empty() definition and re-enable is_empty tests
✓ add tools for future Claude string substitution tasks
✓ add M8UnknownTypeError exception and remove default fallbacks to WAVSYNTH/AHD_ENVELOPE
✓ standardize instrument/modulator enum strings to use uppercase consistently
  ✓ update format_config.yaml to use uppercase keys for instrument and modulator types
  ✓ removed case-insensitive lookup - now using uppercase everywhere
  ✓ updated all tests to use uppercase enum strings consistently
- do enum helpers support a list but also a dict with list values?
- references to "manual" in modulator testing?
- abstraction of helper support to utils to simplify modulator testing
- add constructor enum supoort to modulator
- add mod destination enums
- M8Params >> M8InstrumentParams
- wavsynth shapes
- macrosynth shapes
- sampler play modes
- filter types
- limit types
- constructor support for enum field string values
- int values not found in enums to raise exceptions
- clean up project initialise file paths
- does project.toml include templates
- version checking
- add back version and log
- instrument type classes should have M8 prefix 
- song counts should be in config 
- remove custom IndexError (not needed/used)
- instrument common synthesiser params should be part of config
- instrument read_from_file and write_to_file
- config refactoring
  - modulators section (fields, constants)
  - metadata section (fields)
  - phrases section (fields)
  - chains section (fields)
  - fx section (fields, constants)
- harmonise modulators offset
- remove redundant sample_path_offset in config
- create dump_sampler_m8i script
- avoid sample path duplication
- load m8i and print from project modulator offset
- adapt to print modulators from modulator offset
- remove version
- don't write to var
- bake_chains handling of blanks
- bake_chains script
- remove typing
- concat_phrases script
- validation of flat structures [notes]
- check if project read/write is tested
- refactor modulators as per instruments
- move instruments
- song/chain/phrase example
- sampler example
- macrosynth example
- string handling code smell
- add instrument name
- m8s >> dict test suite
- instrument inspector
- json bitmap
- add back wavsynth param hardcoding
- propose a solution for removing synth param hardcoding
- abstract offsets, counts, sizes to YAML configuration
- remove hardcoded constants in favor of configuration
- instrument, modulator tests
- project tests
- remove defaults and backwards compatibility
- clean up commenting
- CLAUDE.md

