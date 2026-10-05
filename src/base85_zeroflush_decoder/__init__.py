"""Base85 Zeroflush Decoder: encode and decode ZeroMQ Z85."""

from .core import encode, decode, Z85Error

__all__ = ["encode", "decode", "Z85Error"]
