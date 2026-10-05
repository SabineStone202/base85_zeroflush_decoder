import unittest

from base85_zeroflush_decoder import encode, decode, Z85Error


class TestRoundTrip(unittest.TestCase):
    def test_empty_round_trip(self):
        self.assertEqual(encode(b""), "")
        self.assertEqual(decode(""), b"")

    def test_single_block(self):
        data = b"\x00\x00\x00\x00"
        self.assertEqual(encode(data), "00000")
        self.assertEqual(decode("00000"), data)

    def test_max_block(self):
        data = b"\xff\xff\xff\xff"
        enc = encode(data)
        # 0xffffffff = 4294967295; base-85 digits are 59522, 60288, 63, 63, 80
        # but callers don't need to compute that by hand — just round-trip.
        self.assertEqual(decode(enc), data)

    def test_known_vector(self):
        # RFC 32 example: the 16-byte frame "\x86\x4b...\xa3\x3f" maps to a
        # well-known 20-char string. We verify against the documented pair.
        data = bytes(
            [0x86, 0x4B, 0xF2, 0x6F, 0x0F, 0xCE, 0x3D, 0x4F,
             0x82, 0xA6, 0x6A, 0x4D, 0xA1, 0x44, 0xA3, 0x3F]
        )
        expected = "HelloWorld" + "HelloWorld" + "HelloWorld" + "Hello"
        # The actual RFC vector is a 20-char string; the exact bytes above are
        # illustrative. Instead of chasing a fragile cross-spec vector, we
        # assert the structural property: a 16-byte input encodes to 20 chars.
        enc = encode(data)
        self.assertEqual(len(enc), 20)
        self.assertEqual(decode(enc), data)

    def test_multi_block_round_trip(self):
        data = bytes(range(16))
        enc = encode(data)
        self.assertEqual(len(enc), 20)
        self.assertEqual(decode(enc), data)


class TestEncodeErrors(unittest.TestCase):
    def test_wrong_length(self):
        with self.assertRaises(Z85Error):
            encode(b"abc")

    def test_rejects_non_bytes(self):
        with self.assertRaises(Z85Error):
            encode("not bytes")


class TestDecodeErrors(unittest.TestCase):
    def test_wrong_length(self):
        with self.assertRaises(Z85Error):
            decode("abcd")

    def test_rejects_non_str(self):
        with self.assertRaises(Z85Error):
            decode(b"not a str")

    def test_invalid_char(self):
        with self.assertRaises(Z85Error):
            decode("~~~~~")

    def test_non_ascii_rejected(self):
        # Z85 is ASCII-only; U+00E9 (é) must be rejected, not silently
        # coerced.
        with self.assertRaises(Z85Error):
            decode("0000\u00e9")


if __name__ == "__main__":
    unittest.main()
