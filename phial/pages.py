__all__ = ["page", "multipage"]

# stdlib
import codecs
import os.path

# internal
import phial.commands
import phial.utils

# set up logging
import logging
log = logging.getLogger(__name__)


def page(path, command_queue=phial.commands.global_queue):
    def real_decorator(function):
        command_queue.enqueue(BuildPageCommand(function, path))
        return function

    return real_decorator


def multipage(path, foreach, command_queue=phial.commands.global_queue):
    def real_decorator(function):
        command_queue.enqueue(BuildMultiplePagesCommand(function, path, foreach))
        return function

    return real_decorator


class BuildPageCommand(phial.commands.Command):
    def __init__(self, function, path):
        self.function = function
        self.path = path

    def run(self, config):
        output = self.function()
        if output is None:
            log.info("Page function %r returned None.", self.function)
            return

        output_path = os.path.join(config["output"], self.path)
        if not phial.utils.is_path_under_directory(output_path, config["output"]):
            phial.utils.log_and_die(
                "Page's path must be relative and under the output directory. Did you begin your "
                "path with a / or .. ?")

        try:
            os.makedirs(os.path.join(config["output"], os.path.dirname(output_path)))
        except OSError:
            log.debug("Ignoring error making directory for %r.", output_path, exc_info=True)

        logging.info("Writing output of page function %r to %r.", self.function, self.path)
        
        if isinstance(output, unicode):
            with codecs.open(output_path, "w", config["output_encoding"]) as f:
                f.write(output)
        elif isinstance(output, str):
            with open(output_path, "wb") as f:
                f.write(output)
        else:
            phial.utils.log_and_die("Page function must return str or unicode instance")


class PartialFunction(object):
    """Equivalent to ``functools.partial`` but pretty-prints.

        >>> def foo(a, b, c):
        ...    return a + b + c
        ...
        >>> partial = PartialFunction(foo, 1, 2)
        >>> print repr(partial)
        PartialFunction(foo, 1, 2)
        >>> partial(3)
        6

    .. note::

        The wrapped function's ``__name__`` attribute will be used when pretty printing (inside of
        ``PartialFunction.__repr__``). This can be an issue for lambdas (which always have the name
        ``<lambda>``).
    """
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        bound_args = ", ".join([self.function.__name__] + list(str(i) for i in self.args) +
                               ["{!s}={!r}".format(k, v) for k, v in self.kwargs.iteritems()])
        return "PartialFunction({})".format(bound_args)

    def __call__(self, *args, **kwargs):
        computed_kwargs = dict(self.kwargs.items() + kwargs.items())
        return self.function(*(self.args + args), **(computed_kwargs))


class BuildMultiplePagesCommand(phial.commands.Command):
    def __init__(self, function, path, foreach):
        self.function = function
        self.path = path
        self.foreach = foreach

    def run(self, config):
        for i in self.foreach:
            try:
                resolved_path = self.path.format(i)
            except Exception as e:
                phial.utils.log_and_die(
                    "%s raised resolving path string %r for page function %r (item = %r)",
                    e.__class__.__name__, self.path, self.function, i, exc_info=True)

            bound_func = PartialFunction(self.function, resolved_path, i)
            BuildPageCommand(function=bound_func, path=resolved_path).run(config)
