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


def load_preset_yaml(instrument_class, filepath):
    """Load instrument preset from a YAML file.

    The YAML can contain either:
    - Integer enum values (e.g., SHAPE: 0)
    - String enum names (e.g., SHAPE: TRIANGLE)

    Args:
        instrument_class: Instrument class (M8Sampler, M8Wavsynth, etc.)
        filepath: Path to YAML file

    Returns:
        Configured instrument instance
    """
    filepath = Path(filepath)

    with open(filepath, 'r') as f:
        preset_dict = yaml.safe_load(f)

    return instrument_class.from_dict(preset_dict)


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


def load_presets_yaml(instrument_class, preset_dir):
    """Load all YAML presets from a directory.

    Args:
        instrument_class: Instrument class (M8Sampler, M8Wavsynth, etc.)
        preset_dir: Directory containing YAML preset files

    Returns:
        Dict mapping preset names to instrument instances
    """
    preset_dir = Path(preset_dir)
    presets = {}

    for filepath in sorted(preset_dir.glob("*.yaml")):
        preset_name = filepath.stem
        presets[preset_name] = load_preset_yaml(instrument_class, filepath)

    return presets
