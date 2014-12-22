__all__ = ("TemporaryFile", )

# stdlib
import glob
import os.path
import tempfile


def is_path_under_directory(path, directory):
    """Return True if ``path`` is in ``dir``.

    This operates only on paths and does not actually access the filesystem.
    """
    # TODO(brownhead): This might not handle unicode correctly...
    directory = os.path.abspath(directory) + "/"
    path = os.path.abspath(path) + "/"
    return path.startswith(directory)


def glob_foreach_list(foreach, maybe_open_file=lambda path: path):
    """Unified handling of "foreach lists".

    Phial functions that take in a "foreach" argument run that argument through this function to
    make things a little more convenient to the user. The handling is straightforward and will
    basically just glob any strings it finds.
    """
    listified = foreach
    if isinstance(foreach, basestring):
        listified = [foreach]

    # Glob any strings in the list.
    globbed_list = []
    for i in listified:
        if isinstance(i, basestring):
            globbed_list += [maybe_open_file(path) for path in glob.iglob(i)]
        else:
            globbed_list.append(i)

    return globbed_list


class TemporaryFile(tempfile.SpooledTemporaryFile):
    DEFAULT_SPOOL_SIZE = 10 * 1024 * 1024  # 1024 * 1024 is one mebibyte

    def __init__(self, name=None, spool_size=DEFAULT_SPOOL_SIZE):
        self.name = name
        self.spool_size = spool_size
        tempfile.SpooledTemporaryFile.__init__(self, max_size=spool_size)


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        # This is a little racey, but does a good job at reducing massive log spam, so definitely
        # a net win.
        if e.errno != 17 and os.path.isdir(path):
            raise
