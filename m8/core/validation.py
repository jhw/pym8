"""
Validation utilities for the M8 library.

This module provides tools for validating M8 data structures and tracking validation errors.
"""

import logging

class M8ValidationResult:
    """Container for validation results with hierarchical error tracking."""
    
    def __init__(self, context=None):
        self.context = context or "root"
        self.errors = []
        self.valid = True
    
    def add_error(self, message, component=None):
        """Add a validation error with optional component path."""
        path = f"{self.context}.{component}" if component else self.context
        self.errors.append(f"{path}: {message}")
        self.valid = False
        return self
    
    def merge(self, other_result, component=None):
        """Merge another validation result into this one."""
        if not other_result.valid:
            self.valid = False
            
            # Add errors from other result with updated context
            for error in other_result.errors:
                if component:
                    error = error.replace(other_result.context, f"{self.context}.{component}")
                self.errors.append(error)
        
        return self
    
    def raise_if_invalid(self):
        """Raise ValueError if validation failed."""
        if not self.valid:
            error_message = "\n".join(self.errors)
            raise ValueError(error_message)
    
    def log_errors(self, logger=None):
        """Log all validation errors."""
        if not self.valid and logger:
            for error in self.errors:
                logger.error(error)

