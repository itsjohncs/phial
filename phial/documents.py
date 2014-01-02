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

# stdlib
import StringIO

# external
import yaml

# internal
from . import exceptions

_FRONT_MATTER_START = u"---"
"""The string that denotes the beginning of YAML frontmatter."""

_FRONT_MATTER_END = u"..."
"""The string that denotes the end of YAML frontmatter."""

def _consume_frontmatter(the_file):
    """
    Will consume and parse any frontmatter present in the file.

    :returns: A dictionary of template fields that were specified in the
        frontmatter or ``None`` if no frontmatter is present.

    """

    # Check to see if there is YAML frontmatter
    first_line = unicode(the_file.readline()).rstrip()
    if first_line != _FRONT_MATTER_START:
        return None

    # Iterate through every line until we hit the end of the front
    # matter.
    front_matter = StringIO.StringIO()
    for line in the_file:
        uline = unicode(line)
        if uline.rstrip() == _FRONT_MATTER_END:
            break
        else:
            front_matter.write(uline)
    else:
        # This occurs if we didn't break above, so we know that
        # there was no end to the frontmatter. This is illegal.
        raise exceptions.BadFrontmatter(
            path = getattr(the_file, "name", None),
            error_string = u"No end of frontmatter."
        )

    return yaml.load(front_matter)

class Document:
    """
    A Phial document.

    """

    def __init__(self, the_file):
        self.the_file = the_file
        self.frontmatter = _consume_frontmatter(self.the_file)
        self.body = self.the_file.read()
