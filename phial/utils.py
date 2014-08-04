__all__ = ("TemporaryFile", )

# stdlib
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
