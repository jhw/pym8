"""Bit manipulation utilities for M8 binary data."""

def split_byte(byte):
    """Split a byte into upper and lower nibbles (4-bit values)."""
    upper = (byte >> 4) & 0x0F
    lower = byte & 0x0F
    return upper, lower

def join_nibbles(upper, lower):
    """Join two 4-bit nibbles into a single byte."""
    return ((upper & 0x0F) << 4) | (lower & 0x0F)

def get_bits(value, start, length=1):
    """Extract specific bits from a value (0=least significant bit)."""
    mask = (1 << length) - 1
    return (value >> start) & mask

def set_bits(value, bits, start, length=1):
    """Set specific bits in a value (0=least significant bit)."""
    mask = ((1 << length) - 1) << start
    return (value & ~mask) | ((bits & ((1 << length) - 1)) << start)