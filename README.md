# base85-zeroflush-decoder

Encode and decode ZeroMQ Z85 (RFC 32) in pure Python. Exports `encode`, `decode`, and `Z85Error`.

```python
from base85_zeroflush_decoder import encode, decode

assert decode(encode(b"\x00\x01\x02\x03")) == b"\x00\x01\x02\x03"
```

## Why this exists

Z85 is the Ascii85 variant used by ZeroMQ for keys and CURVE handshakes. It has no padding scheme: binary input must be a multiple of 4 bytes, and text must be a multiple of 5 characters. This library enforces both, and rejects characters outside the Z85 alphabet rather than mapping them to zero — silent corruption in a key exchange is the worst possible failure mode, so we fail loudly instead.

## Edge cases

- `encode` raises `Z85Error` if the input length is not a multiple of 4. There is no padding.
- `decode` raises `Z85Error` if the text length is not a multiple of 5 or contains a character outside the Z85 alphabet.
- Empty input is valid and round-trips to empty output.
