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
import codecs

# external
import yaml

# internal
from . import exceptions

# We need to get PyYAML to use the Python unicode object to store any strings
# present in the YAML. Therefore we override the default handling of YAML
# strings here. The default handling will return a str if every character is
# a valid ASCII character.
yaml.SafeLoader.add_constructor(
    u"tag:yaml.org,2002:str",
    lambda loader, node: loader.construct_scalar(node)
)

def open_file(path):
    """
    Open a file with the correct decoder according to the
    `YAML 1.1 spec <http://yaml.org/spec/1.1/#id868742>`_, with the notable
    addition of correct handling of the
    `UTF-8 with BOM signature <http://en.wikipedia.org/wiki/Byte_order_mark#UTF-8>`_
    encoding.

    :param path: The location of the file on the operating system. It will be
        opened for reading only.

    :returns: A file-like object as returned by
        `codecs.open() <http://docs.python.org/2/library/codecs.html#codecs.open>`_.

    """

    DEFAULT_ENCODING = u"utf_8"
    BOMS = [
        (codecs.BOM_UTF8, u"utf_8_sig"),
        (codecs.BOM_UTF16, u"utf_16"),
        (codecs.BOM_UTF16_BE, u"utf_16_be"),
        (codecs.BOM_UTF16_LE, u"utf_16_le)
    ]

    # Grab just enough bytes to determine the encoding
    with open(path, u"rb") as raw_file:
        max_bom_length = reduce(max, [i[0] for i in BOMS])
        front_data = raw_file.read(max_bom_length)

    file_encoding = DEFAULT_ENCODING
    for bom, encoding in BOMS:
        if front_data.startswith(bom):
            file_encoding = encoding
            break

    return codecs.open(path, u"rb", encoding = file_encoding)

def parse_document(document_file):
    """
    Will parse a document into its frontmatter and body components. The
    frontmatter will be decoded with a YAML parser.

    :param document_file: A file-like object to consume. It must produce
        ``unicode`` objects when read from rather than ``str``.

    :returns: A two-tuple ``(frontmatter, body)``.

    """

    FRONT_MATTER_END = u"..."

    # Iterate through every line until we hit the end of the front
    # matter.
    front_matter = StringIO.StringIO()
    for line in document_file:
        assert isinstance(line, unicode)

        front_matter.write(line)

        if line.rstrip() == FRONT_MATTER_END:
            break
    else:
        # This occurs if we didn't break above, so we know that
        # there was no frontmatter after all.
        return (None, front_matter.get_value())

    decoded_front_matter = yaml.safe_load(front_matter)

    # The rest of the file is the body.
    body = document_file.read()

    return (decoded_front_matter, body)

class Document:
    """
    A Phial document.

    :ivar frontmatter: A dictionary containing the parsed frontmatter of the
        document.
    :ivar body: A unicode string containing the body of the document (which is
        defined as everything that's not the frontmatter).
    """

    def __init__(self, document):
        """
        :param document: May be either a path or a file-like object.

        """

        if isinstance(document, basestring):
            document_file = open_file(document)
        else:
            document_file = document

        self.frontmatter, self.body = parse_document(document_file)
