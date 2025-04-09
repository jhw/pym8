# Proposals

## Enum Decorator Refactoring Strategy

### Problem Statement
The current enum handling in the API mixes multiple approaches:
- Direct function calls (`serialize_param_enum_value`, `deserialize_param_enum`)
- Context managers for instrument type context
- Manual enum conversions in serialization/deserialization methods
- A new decorator-based approach (`with_enum_param`) recently added for M8PhraseStep

This inconsistency increases code complexity and makes maintenance more difficult.

### Proposed Solution
Extend the decorator-based approach used in M8PhraseStep to the entire codebase, standardizing enum handling through decorators.

### Benefits
1. Improved abstraction hiding complex enum lookup/conversion logic
2. Reduced code size by eliminating repetitive enum handling
3. Better testability by separating enum conversion from business logic
4. Consistent pattern for enum handling across the codebase
5. Self-documenting methods that clearly advertise enum parameters

### Implementation Strategy

#### Phase 1: Preparation
1. Create a complete set of decorator functions in `m8/core/enums.py`:
   - Extended parameter decorators (`with_enum_param` with broader configurability)
   - Class decorators for bulk enum handling
   - Property decorators for enum-aware getters/setters

2. Define standard patterns for common enum operations:
   - Parameter conversion (input)
   - Return value conversion (output)
   - Dictionary serialization/deserialization
   - Binary data handling

#### Phase 2: API Methods Refactoring
3. Refactor API methods to use decorators, starting with:
   - Remaining phrase methods
   - FX parameter methods
   - Instrument parameter methods

4. Add comprehensive tests for each refactored component

#### Phase 3: Core Data Structure Refactoring
5. Enhance serialization/deserialization methods with appropriate decorators:
   - `as_dict` methods
   - `from_dict` class methods
   - Binary read/write methods

6. Refactor property getters/setters to use enum property decorators

#### Phase 4: Integration and Cleanup
7. Update dependent code to use the new patterns
8. Remove redundant enum handling code
9. Update documentation to reflect the new approach

### Migration Considerations
- Each phase should maintain backward compatibility
- Use automated testing to verify behavior remains consistent
- Introduce changes incrementally, class by class
- Consider creating helper migration tools in the `migrations/` directory

### Example Patterns

```python
# Method parameter decorator (for methods that take enum parameters)
@with_enum_param(param_index=0, enum_type="fx_key")
def add_fx(self, key, value):
    # key is automatically converted from string to numeric value
    ...

# Class decorator (for classes with consistent enum patterns)
@with_enum_class(
    params={"amp": "m8.enums.fmsynth.AmplitudeModulation", 
            "mode": "m8.enums.fmsynth.Mode"}
)
class EnumAwareClass:
    ...

# Property decorators (for enum properties)
@enum_property("m8.enums.fmsynth.FilterType")
def filter_type(self):
    return self._filter_type

@filter_type.setter
def filter_type(self, value):
    self._filter_type = value
```

### Risk Assessment
- **Medium risk**: Complex migration path for deeply nested enum handling
- **Medium effort**: Substantial changes across the codebase
- **High reward**: Significantly improved maintainability and consistency

### Historical Proposals

This file previously contained historical proposals that have been migrated to the more comprehensive ARCHITECTURE.md document.

Please refer to ARCHITECTURE.md for current technical documentation.