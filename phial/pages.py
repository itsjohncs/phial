# stdlib
import codecs
import os.path

# internal
from . import actions
from . import utils

# set up logging
import logging
log = logging.getLogger(__name__)

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

class Page(actions.Action):
    def __init__(self, func, path):
        self.func = func
        self.path = path

    def build(self, config):
        output = self.func()
        if output is None:
            logging.info("Page function %r returned None.", self.func)
            return

        output_path = os.path.join(config["output"], self.path)
        if not utils.is_path_under_directory(output_path, config["output"]):
            utils.log_and_die("Page's path must be relative and under the "
                              "output directory (did you begin your path with "
                              "a / or ..?).")
        
        if isinstance(output, unicode):
            with codecs.open(output_path, "w", config["output_encoding"]) as f:
                f.write(output)
        elif isinstance(output, str):
            with open(output_path, "wb") as f:
                f.write(output)
        else:
            utils.log_and_die("Page function must return str or unicode "
                              "instance")


class PartialFunction(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        bound_args = ", ".join(
            [self.func.__name__] +
            list(str(i) for i in self.args) +
            ["{!s}={!r}".format(k, v) for k, v in self.kwargs.iteritems()])
        return "PartialFunction({})".format(bound_args)

    def __call__(self, *args, **kwargs):
        computed_kwargs = dict(self.kwargs.items() + kwargs.items())
        return self.func(*(self.args + args), **(computed_kwargs))


class MultiPage(actions.Action):
    def __init__(self, func, path, foreach):
        self.func = func
        self.path = path
        self.foreach = foreach

    def build(self, config):
        pages = []
        for i in self.foreach:
            try:
                resolved_path = self.path.format(i)
            except Exception as e:
                utils.log_and_die(
                    "%s raised resolving path string %r for page function %r "
                    "(item = %r)", e.__class__.__name__, self.path, self.func,
                    i, exc_info=True)

            bound_func = PartialFunction(self.func, resolved_path, i)
            pages.append(Page(func=bound_func, path=resolved_path))

        for i in pages:
            i.build(config)
