# Copyright (c) 2013 John Sullivan
# Copyright (c) 2013 Other contributers as noted in the CONTRIBUTERS file
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

# A list of sample pages we will use to test our sample parser.
SAMPLE_FILES = [
    {
        # The raw text of the file. This is using the automatic string
        # concatenation feature of Python. More info at
        # http://stackoverflow.com/a/10660443/1989056.
        "raw": (
            "---\n"
            "key1: value1\n"
            "key2: value2\n"
            "...\n"
            "\n"
            "Destruction."
        ),

        # The frontmatter the parser *should* pull out from the document above
        "frontmatter": {"key1": "value1", "key2": "value2"},

        # The body of the file the parser *should* pull out (the body is
        # everything but the frontmatter)
        "body": "\nDestruction."
    },
    {
        "raw": "Small file.",
        "frontmatter": None,
        "body": "Small file."
    }
]

class TestFiles:
    @pytest.mark.parametrize("sample", SAMPLE_FILES)
    def test_frontmatter_parsing(self, sample):
        """Ensure that frontmatter is parsed correctly."""

        # Use a StringIO object to fake out the File class into thinking it's
        # working with a real file.
        fake_file = StringIO.StringIO(sample["raw"])

        f = documents.Document(fake_file)
        assert f.frontmatter == sample["frontmatter"]
