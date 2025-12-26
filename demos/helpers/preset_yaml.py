"""
YAML preset helpers for M8 instruments.

Provides functions to save/load instrument presets as human-readable YAML files.
Uses enum_mode='name' to serialize enum values as readable string names instead
of opaque integers.
"""

import yaml
from pathlib import Path


def save_preset_yaml(instrument, filepath):
    """Save instrument preset to a YAML file with human-readable enum names.

    Args:
        instrument: M8 instrument (Sampler, Wavsynth, etc.)
        filepath: Path to output YAML file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Export with human-readable enum names
    preset_dict = instrument.to_dict(enum_mode='name')

    with open(filepath, 'w') as f:
        yaml.dump(preset_dict, f, default_flow_style=False, sort_keys=False)


def load_preset_yaml(filepath, instrument_class=None):
    """Load instrument preset from a YAML file.

    The YAML can contain either:
    - Integer enum values (e.g., SHAPE: 0)
    - String enum names (e.g., SHAPE: TRIANGLE)

    If the YAML contains a 'type' field and no instrument_class is specified,
    the appropriate instrument class will be auto-detected.

    Args:
        filepath: Path to YAML file
        instrument_class: Optional instrument class (M8Sampler, M8Wavsynth, etc.).
                         If not provided, type is read from YAML 'type' field.

    Returns:
        Configured instrument instance
    """
    filepath = Path(filepath)

    with open(filepath, 'r') as f:
        preset_dict = yaml.safe_load(f)

    if instrument_class:
        # Explicit class specified - use it directly
        return instrument_class.from_dict(preset_dict)
    else:
        # No class specified - use factory pattern (requires 'type' in YAML)
        from m8.api.instrument import M8Instrument
        return M8Instrument.from_dict(preset_dict)


def save_presets_yaml(presets, output_dir):
    """Save multiple presets to individual YAML files.

    Args:
        presets: Dict mapping preset names to instrument instances
        output_dir: Directory to save YAML files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, instrument in presets.items():
        filepath = output_dir / f"{name}.yaml"
        save_preset_yaml(instrument, filepath)


def load_presets_yaml(preset_dir, instrument_class=None):
    """Load all YAML presets from a directory.

    Args:
        preset_dir: Directory containing YAML preset files
        instrument_class: Optional instrument class (M8Sampler, M8Wavsynth, etc.).
                         If not provided, type is read from each YAML's 'type' field.

    Returns:
        Dict mapping preset names to instrument instances
    """
    preset_dir = Path(preset_dir)
    presets = {}

    for filepath in sorted(preset_dir.glob("*.yaml")):
        preset_name = filepath.stem
        presets[preset_name] = load_preset_yaml(filepath, instrument_class)

    return presets
