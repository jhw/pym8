# Proposals

## Modulator Parameter Handling Refactoring

### Problem Diagnosis
Through debugging the modulator parameters, specifically the decay parameter in AHD_ENVELOPE modulators, we've identified a critical mismatch between parameter offsets defined in the configuration and the block size used for binary storage.

#### Key Issues
1. **Offset vs Block Size Mismatch**: 
   - The modulator block size is defined as 6 bytes in format_config.yaml
   - The decay parameter has offset 4, meaning it should be stored at position 6 (2+4) 
   - This position is outside the 6-byte block size, causing the value to be lost

2. **Inconsistent Parameter Placement**:
   - Parameters like 'decay' are configured with offsets that would place them outside the fixed block size
   - When writing, these parameters are properly set in memory but not correctly encoded in the binary data
   - When reading, the parameters aren't found because they're outside the fixed block size

3. **Offset-based vs Position-based Parameters**:
   - The code tries to map parameters by offset, but this approach breaks for parameters with offsets that would place them beyond the block size
   - There's no consistent mapping between parameter offsets and their actual positions in the binary data

### Proposed Solution
Implement a fixed parameter positioning approach that ensures consistent binary layout regardless of the offsets defined in the configuration.

#### Key Components

1. **Fixed Position Mapping**:
   Create a mapping dictionary that explicitly assigns each parameter to a fixed position within the block:
   ```python
   # For AHD_ENVELOPE
   name_to_position = {
       "attack": 2,    # Always at position 2
       "hold": 3,      # Always at position 3  
       "decay": 4,     # Always at position 4
       # position 5 for other params
   }
   
   # For LFO
   name_to_position = {
       "oscillator": 2,    # Always at position 2
       "trigger": 3,        # Always at position 3  
       "frequency": 4,      # Always at position 4
       # position 5 for other params  
   }
   ```

2. **Consistent Write/Read Methods**:
   - Modify M8Modulator.write() to use the fixed positions when writing parameters
   - Update M8Modulator.read() to use the same fixed positions when reading
   - Ensure the same mapping is used in both directions

3. **Maintain Fixed Block Size**:
   - Keep the BLOCK_SIZE constant at 6 bytes
   - Ensure all parameters fit within this fixed block size

4. **Parameter Prioritization**:
   - For parameters that don't fit naturally, use a consistent priority order
   - Ensure most important parameters get preserved in the available positions

### Implementation Strategy

1. **Update M8Modulator.write()**:
   - Define fixed position mappings
   - Write common fields (type, destination, amount)
   - Place each parameter in its fixed position

2. **Update M8Modulator.read()**:
   - Use the same fixed position mappings
   - Read each parameter from its fixed position
   - Don't rely on offset-based reads for parameters

3. **Documentation**:
   - Add clear documentation about the fixed parameter positioning
   - Document the relationship between format_config.yaml offsets and actual binary positions

### Benefits
1. Consistent parameter handling regardless of offsets in config
2. More reliable serialization/deserialization 
3. Easier to understand and debug
4. Maintains the fixed block size requirement

### Testing
1. Test with parameters that have offsets exceeding block size
2. Verify roundtrip consistency (write->read->write)
3. Test all modulator types

### Risk Assessment
- **Low risk**: Changes contained to modulator handling code
- **Medium effort**: Requires careful mapping of all parameters
- **High reward**: Fixes a critical bug in modulator parameter handling

## Enum Decorator Refactoring Strategy

### Problem Statement
The current enum handling in the API mixes multiple approaches:
- Direct function calls (`serialize_param_enum_value`, `deserialize_param_enum`)
- Context managers for instrument type context
- Manual enum conversions in serialization/deserialization methods
- A new decorator-based approach (`with_enum_param`) recently added for M8PhraseStep

This inconsistency increases code complexity and makes maintenance more difficult.

[... rest of existing enum decorator proposal ...]