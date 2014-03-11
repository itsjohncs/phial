# Copyright (c) 2013-2014 John Sullivan
# Copyright (c) 2013-2014 Other contributers as noted in the CONTRIBUTERS file
#
# This file is part of Phial
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

# A list of sample pages we will use to test our sample parser.
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

        # The body of the file the parser *should* pull out (the body is
        # everything but the frontmatter)
        "body": u"\nDestruction."
    },
    {
        "raw": u"",
        "frontmatter": None,
        "body": u""
    },
    {
        "raw": UNICODE_TEST_PONY,
        "frontmatter": None,
        "body": UNICODE_TEST_PONY
    }
]

TEST_ENCODINGS = [
    # (write_encoding, BOM, read_encoding)
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
        """Ensure that frontmatter is parsed correctly."""

        # Use a StringIO object to fake out the Documents class into thinking
        # it's working with a real file.
        fake_file = StringIO.StringIO(sample["raw"])

        f = documents.Document(fake_file)
        assert f.frontmatter == sample["frontmatter"]

    @pytest.mark.parametrize("encoding", TEST_ENCODINGS)
    def test_open_file(self, encoding):
        encoded_pony = encoding[1] + UNICODE_TEST_PONY.encode(encoding[0])
        print repr(encoded_pony)

        with tempfile.NamedTemporaryFile(delete = False) as f:
            f.write(encoded_pony)
            delete_path = f.name

        try:
            with documents.open_file(f.name) as f:
                result = f.read()
                result_encoding = f.encoding
        finally:
            os.remove(delete_path)

        assert f.encoding == encoding[2]
        assert result == UNICODE_TEST_PONY
