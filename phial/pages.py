from collections import namedtuple

def register_page(func, *args, **kwargs):
    _pages.append(_Page(func, *args, **kwargs))

def page(*dec_args, **dec_kwargs):
    # The way decorators with arguments work is that we need to return another
    # decorator that takes in a function, then that decorator will be applied
    # to the function.
    def real_decorator(function):
        # The only thing this decorator does is add the function and its
        # arguments to the list of known pages.
        register_page(function, *dec_args, **dec_kwargs)

        # We don't do the typical decorator thing of wrapping the function so
        # just return the function unchanged.
        return function

    return real_decorator

class _Page:
    def __init__(self, func, url = None, files = None):
        """
        :param func: The function that will be called to generate the page.
        :param url: The desired relative URL of the page. If `None`, a URL must
                be specified in `func`'s return value.
        :param files: May be `None`, a string, or a list of strings.  If a
                string, that string will be globbed and `func` will be called
                for each unique matching file. If a list of strings, each
                string in the list will be globbed and then `func` will be
                called for each unique matching file. If `None`, `func` will be
                called only once.
        """

        self.func = func
        self.url = url
        self.files = files

    def glob_files(self):
        import glob
        files = glob.glob(page.files)

        log.debug("Globbed %s and got %s", repr(page.files), repr(files))

_pages = []
