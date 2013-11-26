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

# external
import yaml

_FRONT_MATTER_MARKER = u"---"
"""The string that denotes the beginning and end of YAML front matter."""

class File:
    """
    A Phial file.
    """

    def __init__(self, file_handle):
        self.file_handle = file_handle

    def _parse_frontmatter(self):
        """
        Will consume and parse any front matter present in the file. Returns a
        dictionary of template fields that were specified in the front matter
        or `None` if no front matter is present.

        """

        # Check to see if there is YAML front matter
        first_line = unicode(self.file_handle.readline()).rstrip()
        if first_line != _FRONT_MATTER_MARKER:
            return None

        # Iterate through every line until we hit the end of the front
        # matter.
        import StringIO
        front_matter = StringIO.StringIO()
        for line in self.file_handle:
            uline = unicode(line)
            if uline.rstrip() == _FRONT_MATTER_MARKER:
                break
            else:
                front_matter.write(uline)
        else:
            # This occurs if we didn't break above, so we know that
            # there was no end to the front matter. This is illegal.
            raise exceptions.BadFrontMatter(
                path = self.file_handle.name,
                error_string = "No end of front matter."
            )

        # Make sure everything we've done is reflected in the string then
        # move to the beginning of the "file".
        front_matter.flush()
        front_matter.seek(0)

        return yaml.load(front_matter)

    def __getitem__(self, attribute):
        return self.attributes[attribute]

    def __contains__(self, attribute):
        return attribute in self.attributes
