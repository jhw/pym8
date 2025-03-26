"""Compatibility module for accessing the instrument context manager.

This module is preserved for backwards compatibility with existing code.
For new code, import M8InstrumentContext directly from m8.api.utils.enums.
"""

from m8.api.utils.enums import M8InstrumentContext, _InstrumentContextBlock

# Export the same classes/functions as before
__all__ = ['M8InstrumentContext', '_InstrumentContextBlock']
