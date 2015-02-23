# stdlib
import glob
import os.path
import sys
import tempfile


def public(f):
    """"Use a decorator to avoid retyping function/class names.

    * Grabbed from recipe by Sam Denton
    http://code.activestate.com/recipes/576993-public-decorator-adds-an-item-to-__all__/
    * Based on an idea by Duncan Booth:
    http://groups.google.com/group/comp.lang.python/msg/11cbb03e09611b8a
    * Improved via a suggestion by Dave Angel:
    http://groups.google.com/group/comp.lang.python/msg/3d400fb22d8a42e1
    """
    all = sys.modules[f.__module__].__dict__.setdefault('__all__', [])
    if f.__name__ not in all:  # Prevent duplicates if run from an IDE.
        all.append(f.__name__)
    return f
public(public)


def is_path_under_directory(path, directory):
    """Return True if ``path`` is in ``dir``.

    This operates only on paths and does not actually access the filesystem.
    """
    # TODO(brownhead): This might not handle unicode correctly...
    directory = os.path.abspath(directory) + "/"
    path = os.path.abspath(path) + "/"
    return path.startswith(directory)


def glob_foreach_list(foreach):
    """Globs a path/paths and return the flattened result.

    :param foreach: The path(s) to glob.
    :type foreach: list, str, or unicode
    :return: The sorted list of paths.

    :Example:

    >>> glob_foreach_list(["b/*", "a"])
    ["a", "b/1", "b/2"]
    >>> glob_foreach_list("b/*")
    ["b/1", "b/2"]
    """
    listified = foreach
    if isinstance(foreach, basestring):
        listified = [foreach]

    # Glob any strings in the list.
    globbed_list = []
    for i in listified:
        if isinstance(i, basestring):
            globbed_list += glob.glob(i)
        else:
            globbed_list.append(i)

    return sorted(globbed_list)


@public
class file(tempfile.SpooledTemporaryFile):
    DEFAULT_SPOOL_SIZE = 10 * 1024 * 1024  # 1024 * 1024 is one mebibyte

    def __init__(self, name=None, spool_size=DEFAULT_SPOOL_SIZE, content=None):
        print name, content
        self.name = name
        self.spool_size = spool_size
        tempfile.SpooledTemporaryFile.__init__(self, max_size=spool_size)
        if content is not None:
            self.write(content)
            self.seek(0)


# HACK(brownhead): I should stabilize on a single name.
TemporaryFile = file


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        # This is a little racey, but does a good job at reducing massive log spam, so definitely
        # a net win.
        if e.errno != 17 and os.path.isdir(path):
            raise


@public
def basename_noext(path):
    return os.path.splitext(os.path.basename(path))[0]
