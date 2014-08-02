__all__ = ["TemporaryFile"]

# stdlib
import glob
import os.path
import tempfile


def is_path_under_directory(path, directory):
    """Returns True if ``path`` is in ``dir``.

    This operates only on paths and does not actually access the filesystem.
    """
    # TODO(brownhead): This might not handle unicode correctly...
    directory = os.path.abspath(directory) + "/"
    path = os.path.abspath(path) + "/"
    return path.startswith(directory)


# TODO(brownhead): Spruce this up so we just get log message with a traceback
# included. It might be worthwhile to get fancy and cut off the last frame
# (this one) to avoid the common confusion of the last frame being pretty
# useless.
def log_and_die(logging_module, *args, **kwargs): 
    logging_module.error(*args, **kwargs)
    raise RuntimeError()


class TemporaryFile(tempfile.SpooledTemporaryFile):
	DEFAULT_SPOOL_SIZE = 10 * 1024 * 1024 # 1024 * 1024 is one mebibyte

	def __init__(self, name=None, spool_size=DEFAULT_SPOOL_SIZE):
		self.name = name
		self.spool_size = spool_size
		tempfile.SpooledTemporaryFile.__init__(self, max_size=spool_size)
