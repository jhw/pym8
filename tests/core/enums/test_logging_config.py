"""
Configure logging for enum tests to suppress common context warnings.
This module should be imported in each test module to configure logging properly.
"""

import logging

# Configure logging to suppress "No instrument_type provided and none found in context" warnings
logging.getLogger("m8.core.enums").setLevel(logging.ERROR)