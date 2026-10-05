"""Core encode/decode for ZeroMQ Z85 encoding.

Z85 is an Ascii85 variant published as part of the ZeroMQ RFC 32 spec.
The alphabet differs from classic Ascii85 and the framing rule is
strict: binary input must be a multiple of 4 bytes, and text input
must be a multiple of 5 characters. We enforce both because leniency
here would silently corrupt data on round-trip.

The decoder rejects characters outside the Z85 alphabet rather than
mapping them to zero, because accepting stray bytes is the sort of
silent corruption that ruins keys and CURVE handshakes.
"""

# The Z85 alphabet, as defined in ZeroMQ RFC 32. It is NOT the same as
# the Ascii85 alphabet: it deliberately drops quote, backslash, and a few
# others so the output can live inside C string literals and JSON without
# escaping.
_ALPHABET = (
    "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ".-:+=^!/*?&<>()[]{}@%$#"
)

# Precompute the reverse lookup once. 255 is used as the sentinel for
# "not in alphabet" because it is outside the byte range, so a simple
# bounds check followed by a lookup is all the validation we need.
_REV = [255] * 256
for _i, _c in enumerate(_ALPHABET):
    _REV[ord(_c)] = _i
del _i, _c


class Z85Error(ValueError):
    """Raised on malformed input to encode or decode.

    Subclasses ValueError so callers doing broad validation still catch it.
    """


def encode(data: bytes) -> str:
    """Encode bytes to a Z85 string.

    len(data) must be a multiple of 4; Z85 has no padding scheme.
    Raises Z85Error otherwise.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise Z85Error("encode expects bytes-like input")
    if len(data) % 4 != 0:
        raise Z85Error(
            f"Z85 input length must be a multiple of 4, got {len(data)}"
        )

    out = []
    # Walk 4 bytes at a time, pack into one 32-bit unsigned int, then
    # pull five base-85 digits out of it. Using int.from_bytes keeps this
    # endian-explicit and avoids struct quirks.
    for i in range(0, len(data), 4):
        chunk = data[i : i + 4]
        value = int.from_bytes(chunk, "big")
        # Unroll into five characters, most significant first, so the
        # decoder's inverse (value = c0*85^4 + ...) lines up exactly.
        out.append(_ALPHABET[(value // (85 ** 4)) % 85])
        out.append(_ALPHABET[(value // (85 ** 3)) % 85])
        out.append(_ALPHABET[(value // (85 ** 2)) % 85])
        out.append(_ALPHABET[(value // 85) % 85])
        out.append(_ALPHABET[value % 85])
    return "".join(out)


def decode(text: str) -> bytes:
    """Decode a Z85 string to bytes.

    len(text) must be a multiple of 5. Characters must all be in the Z85
    alphabet. Raises Z85Error otherwise.
    """
    if not isinstance(text, str):
        raise Z85Error("decode expects str input")
    if len(text) % 5 != 0:
        raise Z85Error(
            f"Z85 text length must be a multiple of 5, got {len(text)}"
        )

    # Fast path for the common case: ASCII only. We materialize a bytes
    # copy so we can index without per-char ord() calls in the loop.
    try:
        raw = text.encode("ascii")
    except UnicodeEncodeError as exc:
        # Non-ASCII cannot be valid Z85; surface a clear error.
        raise Z85Error(f"non-ASCII character in Z85 text: {exc.reason}") from exc

    out = bytearray()
    for i in range(0, len(raw), 5):
        chunk = raw[i : i + 5]
        value = 0
        for c in chunk:
            v = _REV[c]
            if v == 255:
                raise Z85Error(
                    f"character {chr(c)!r} is not in the Z85 alphabet"
                )
            value = value * 85 + v
        # value is at most 85**5 - 1 = 4,437,053,124, which fits in a
        # uint32; clamp just in case a buggy alphabet somehow pushed it
        # over. This is belt-and-braces; the alphabet length is fixed.
        value &= 0xFFFFFFFF
        out += value.to_bytes(4, "big")
    return bytes(out)
