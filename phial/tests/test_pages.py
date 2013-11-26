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
import phial.files

# external
import pytest

# stdlib
import StringIO

SAMPLE_PAGES = [
    {
        "body":
"""---
key1: value1
key2: value2
---

Destruction.""",
        "front_matter": {"key1": "value1", "key2": "value2"},
    },
    {
        "body": "Small file.",
        "front_matter": None,
        "body": "Small file."
    },

]

class TestPages:
    @pytest.mark.parametrize("page", SAMPLE_PAGES)
    def test_frontmatter_parsing(self, page):
        """
        Ensure that frontmatter is parsed correctly.

        """

        # Use a StringIO object to fake out the File class into thinking it's
        # working with a real file.
        fake_file = StringIO.StringIO(page["body"])

        f = phial.files.File(fake_file)
        assert f._parse_frontmatter() == page["front_matter"]
