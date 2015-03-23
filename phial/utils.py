# stdlib
import glob
import os.path
import sys


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

    An IOError will be raised if no results are found for a particular glob.

    :param foreach: The path(s) to glob.
    :type foreach: list, str, or unicode
    :return: The sorted list of paths.

    :Example:

    >>> glob_foreach_list(["b/*", "a"])
    ["a", "b/1", "b/2"]
    >>> glob_foreach_list("b/*")
    ["b/1", "b/2"]
    >>> glob_foreach_list([])
    []
    """
    listified = foreach
    if isinstance(foreach, basestring):
        listified = [foreach]

    # Glob any strings in the list.
    globbed_list = []
    for i in listified:
        if isinstance(i, basestring):
            found = glob.glob(i)
            if not found:
                raise IOError("No files found matching glob {0!r}".format(i))
            globbed_list += found
        else:
            globbed_list.append(i)

    return sorted(globbed_list)


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        # This is a little racey, but does a good job at reducing massive log spam, so definitely
        # a net win.
        if e.errno != 17 and os.path.isdir(path):
            raise


@public
def swap_extension(path, new_extension):
    return os.path.splitext(path)[0] + new_extension
