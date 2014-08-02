# test helpers
from .. import documents

# external
import pytest

# stdlib
import StringIO
import tempfile
import os
import codecs

UNICODE_TEST_PONY = (
    u"TH\u0318E\u0344\u0309\u0356 \u0360P\u032f\u034d\u032dO\u031a\u200bN"
    u"\u0310Y\u0321"
)

SAMPLE_FILES = [
    {
        # The raw text of the file. This is using the automatic string
        # concatenation feature of Python. More info at
        # http://stackoverflow.com/a/10660443/1989056.
        "raw": (
            u"key1: value1\n"
            u"key2: value2\n"
            u"...\n"
            u"\n"
            u"Destruction."
        ),

        # The frontmatter the parser *should* pull out from the document above
        "frontmatter": {u"key1": u"value1", u"key2": u"value2"},

        # The content of the file the parser *should* pull out (the content is
        # everything but the frontmatter)
        "content": u"\nDestruction."
    },
    {
        "raw": u"",
        "frontmatter": None,
        "content": u""
    },
    {
        "raw": UNICODE_TEST_PONY,
        "frontmatter": None,
        "content": UNICODE_TEST_PONY
    }
]

# Each encoding is a tuple of (write_encoding, BOM, read_encoding)
TEST_ENCODINGS = [
    ("utf_8", "", "utf_8"),
    ("utf_8_sig", "", "utf_8_sig"),
    ("utf_16", "", "utf_16"),

    # We have to add the BOM ourselves for these formats because the UTF-16-BE
    # and LE codecs do not add the BOM, only the utf_16 codec does. See
    # http://en.wikipedia.org/wiki/Byte_order_mark#UTF-16 for more info.
    ("utf_16_be", codecs.BOM_UTF16_BE, "utf_16"),
    ("utf_16_le", codecs.BOM_UTF16_LE, "utf_16")
]


class TestDocuments:
    @pytest.mark.parametrize("sample", SAMPLE_FILES)
    def test_frontmatter_parsing(self, sample):
        fake_file = StringIO.StringIO(sample["raw"])

        frontmatter, content = documents.parse_document(fake_file)

        assert frontmatter == sample["frontmatter"]
        assert content.read() == sample["content"]

    @pytest.mark.parametrize("encoding", TEST_ENCODINGS)
    def test_open_file(self, encoding):
        encoded_pony = encoding[1] + UNICODE_TEST_PONY.encode(encoding[0])
        print repr(encoded_pony)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(encoded_pony)
            delete_path = f.name

        try:
            assert documents.detect_encoding(f.name) == encoding[2]
            with documents.open_file(f.name) as f:
                result = f.read()
        finally:
            os.remove(delete_path)

        assert f.encoding == encoding[2]
        assert result == UNICODE_TEST_PONY
