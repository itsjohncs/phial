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
__all__ = [
    "detect_encoding",
    "Document",
    "open_file",
    "parse_document",
    "unicodify_file_object",
]

# stdlib
import codecs
import os
import shutil
import tempfile

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


def detect_encoding(path):
    """Returns encoding of file at path.

    This is not a general purpose function and will not detect all encodings
    (and in fact can only detect a few). It follows the
    `YAML 1.1 spec <http://yaml.org/spec/1.1/#id868742>`_ with the notable
    addition of correct hadnling of the
    `UTF-8 with BOM signature <http://en.wikipedia.org/wiki/Byte_order_mark#UTF-8>`_
    encoding.

    If this function cannot determine the encoding, it will return the default
    encoding ``u"utf_8"``.

    :param path: Path to the file.

    :returns: An encoding name (as a unicode object) from the list under
        `Standard Encodings <https://docs.python.org/2/library/codecs.html#standard-encodings>`_.
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

    return file_encoding


def open_file(path, mode="r"):
    """Opens a file with the correct encoding.

    :func:`detect_encoding` will be used to determine the encoding, then the
    file will be opened with
    `codecs.open() <http://docs.python.org/2/library/codecs.html#codecs.open>`_.

    :param path: Path to the file.

    :returns: A file-like object as returned by
        `codecs.open() <http://docs.python.org/2/library/codecs.html#codecs.open>`_.
    """
    if "b" in mode:
        raise ValueError("Binary mode is not supported.")

    return codecs.open(path, mode, encoding=detect_encoding(path))


# TODO(brownhead): I don't think emit is really the right verb here.
def unicodify_file_object(file_object, encoding="utf_8"):
    """Wraps a file object to accept and emit unicode.

    This is done by invisibly encoding unicode strings into ``encoding`` before
    writing, and decoding into unicode string after reading.

    :param file_object: Any file-like object that accepts and emits ``str``
        objects.

    :returns: A wrapped file-like object.
    """
    info = codecs.lookup(encoding)
    return codecs.StreamReaderWriter(file_object, info.streamreader,
                                     info.streamwriter, "strict")


def parse_document(document_file):
    """Parses a document's frontmatter and contents.

    Will parse a document into its frontmatter and content components. The
    frontmatter will be decoded with a YAML parser.

    :param document_file: A file-like object to consume. It must produce
        ``unicode`` objects when read from rather than ``str`` (see
        :func:`open_file`).

    :returns: A two-tuple ``(frontmatter, content)`` where ``frontmatter`` will
        be whatever the YAML decoder gave us and ``content`` is a file-like
        object containing the content.
    """
    FRONT_MATTER_END = u"..."
    SPOOL_MAX_SIZE = 4 * 1024 * 1024 # Four mebibytes

    # Iterate through every line until we hit the end of the front
    # matter.
    front_matter = unicodify_file_object(
        tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_SIZE))
    for line in document_file:
        assert isinstance(line, unicode)

        front_matter.write(line)

        # Check if this line is the end of the frontmatter, ignoring trailing
        # white space.
        if line.rstrip() == FRONT_MATTER_END:
            break
    else:
        # This occurs if we didn't break above, so we know that there was no
        # frontmatter after all.
        document_file.seek(0)
        return (None, document_file)

    front_matter.seek(0)
    decoded_front_matter = yaml.load(front_matter.read(),
                                     UnicodeSafeLoader)

    content_file = unicodify_file_object(
        tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_SIZE))

    shutil.copyfileobj(document_file, content_file)

    content_file.seek(0)
    return (decoded_front_matter, content_file)
