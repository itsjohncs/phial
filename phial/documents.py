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

# These are the only symbols that will be imported when
# `from documents import *` is used.
__all__ = ["open_file", "parse_document", "Document"]

# stdlib
import StringIO
import codecs
import os

# external
import yaml

# internal
from . import exceptions

class UnicodeSafeLoader(yaml.SafeLoader):
    """YAML loader that uses unicode rather than str.

    We need to get PyYAML to use the Python unicode object to store any strings
    present in the YAML. Therefore we override the default handling of YAML
    strings here. The default handling will return a str if every character is
    a valid ASCII character.
    """

    yaml_constructors = {
        u"tag:yaml.org,2002:str":
            lambda loader, node: loader.construct_scalar(node)
    }

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
        (codecs.BOM_UTF16_BE, u"utf_16"),
        (codecs.BOM_UTF16_LE, u"utf_16")
    ]

    # Grab just enough bytes to determine the encoding
    with open(path, u"rb") as raw_file:
        max_bom_length = reduce(max, [len(i[0]) for i in BOMS])
        front_data = raw_file.read(max_bom_length)

    file_encoding = DEFAULT_ENCODING
    for bom, encoding in BOMS:
        if front_data.startswith(bom):
            file_encoding = encoding
            break

    return codecs.open(path, "r", encoding = file_encoding)

def parse_document(document_file):
    """
    Will parse a document into its frontmatter and content components. The
    frontmatter will be decoded with a YAML parser.

    :param document_file: A file-like object to consume. It must produce
        ``unicode`` objects when read from rather than ``str``.

    :returns: A two-tuple ``(frontmatter, content)``.

    """

    FRONT_MATTER_END = u"..."

    # Iterate through every line until we hit the end of the front
    # matter.
    front_matter = StringIO.StringIO()
    for line in document_file:
        assert isinstance(line, unicode)

        front_matter.write(line)

        # Check if this line is the end of the frontmatter, ignoring *trailing*
        # white space.
        if line.rstrip() == FRONT_MATTER_END:
            break
    else:
        # This occurs if we didn't break above, so we know that there was no
        # frontmatter after all.
        document_file.seek(0)
        return (None, document_file.read())

    decoded_front_matter = yaml.load(
        front_matter.getvalue(), UnicodeSafeLoader)

    # The rest of the file is the content. Note that we have to do multiple reads
    # here. Not entirely sure why yet but I suspect an internal buffer used by
    # the file's next() function.
    content = document_file.read()
    while True:
        data = document_file.read()
        if data == "":
            break
        content += data

    return (decoded_front_matter, content)

class Document:
    """
    A Phial document.

    :ivar file_path: If applicable, the path to the document on the filesystem,
        may be ``None``.
    :ivar frontmatter: A dictionary containing the parsed frontmatter of the
        document.
    :ivar content: A unicode string containing the content of the document (which is
        defined as everything that's not the frontmatter).
    """

    def __init__(self, document, file_path = None):
        """
        :param document: May be either a path or a file-like object.

        """

        if isinstance(document, basestring):
            self.file_path = os.path.abspath(document)
            document_file = open_file(document)
        else:
            self.file_path = None
            document_file = document

        self.frontmatter, self.content = parse_document(document_file)
