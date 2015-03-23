# stdlib
import codecs
import shutil

# external
import yaml

# internal
from . import utils


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


@utils.public
def detect_encoding(path):
    """Return encoding of file at path.

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


@utils.public
def open_file(path, mode="r"):
    """Open a file with the correct encoding.

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
@utils.public
def unicodify_file_object(file_object, encoding="utf_8"):
    """Wrap a file object to accept and emit unicode.

    This is done by invisibly encoding unicode strings into ``encoding`` before
    writing, and decoding into unicode string after reading.

    :param file_object: Any file-like object that accepts and emits ``str``
        objects.

    :returns: A wrapped file-like object.
    """
    info = codecs.lookup(encoding)
    return codecs.StreamReaderWriter(file_object, info.streamreader,
                                     info.streamwriter, "strict")


@utils.public
def parse_frontmatter(document):
    """Parse a document's frontmatter and contents.

    Will parse a document into its frontmatter and content components. The
    frontmatter will be decoded with a YAML parser.

    :param document: A path or a file-like object to consume. The file-like
        object must produce ``unicode`` objects when read from rather than
        ``str`` (see :func:`open_file`).

    :returns: A two-tuple ``(frontmatter, content)`` where ``frontmatter`` will
        be whatever the YAML decoder gave us and ``content`` is a file-like
        object containing the content.
    """
    if isinstance(document, basestring):
        document = open_file(document)

    FRONT_MATTER_END = u"..."

    # Iterate through every line until we hit the end of the front
    # matter.
    front_matter = unicodify_file_object(utils.TemporaryFile())
    for line in document:
        assert isinstance(line, unicode)

        front_matter.write(line)

        # Check if this line is the end of the frontmatter, ignoring trailing
        # white space.
        if line.rstrip() == FRONT_MATTER_END:
            break
    else:
        # This occurs if we didn't break above, so we know that there was no
        # frontmatter after all.
        document.seek(0)
        return (None, document)

    front_matter.seek(0)
    decoded_front_matter = yaml.load(front_matter.read(), UnicodeSafeLoader)

    content_file = unicodify_file_object(utils.TemporaryFile())

    shutil.copyfileobj(document, content_file)

    content_file.seek(0)
    return (decoded_front_matter, content_file)
