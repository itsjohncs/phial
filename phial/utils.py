# stdlib
import glob

def glob_files(files):
    """
    Returns a list of files matching the pattern(s) in ``files``.

    :param files: May be either a string or a list of strings. If a string, the
        pattern will be globbed and all matching files will be returned. If a
        list of strings, all of the patterns will be globbed and all unique
        file paths will be returned.

    :returns: A list of file paths.

    """

    if isinstance(files, basestring):
        result = glob.glob(files)
    else:
        # Glob every pattern and grab the unique results
        result_set = set()
        for i in files:
            result_set.update(glob.glob(i))
        result = list(result_set)

    return result
