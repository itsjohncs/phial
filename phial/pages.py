__all__ = ("page", "multipage", "basename_noext", )

# stdlib
import codecs
import glob
import os.path

# internal
import phial.commands
import phial.utils

# set up logging
import logging
log = logging.getLogger(__name__)


def page(target, command_queue=phial.commands.global_queue):
    def real_decorator(function):
        command_queue.enqueue(BuildPageCommand(function, target))
        return function

    return real_decorator


def basename_noext(path):
    return os.path.splitext(os.path.basename(path))[0]


def multipage(target, foreach, preformat=basename_noext,
              command_queue=phial.commands.global_queue):
    def real_decorator(function):
        command_queue.enqueue(BuildMultiplePagesCommand(function, target, foreach, preformat))
        return function

    return real_decorator


class BuildPageCommand(phial.commands.Command):
    def __init__(self, function, target):
        self.function = function
        self.target = target

    def run(self, config):
        output = self.function()
        if output is None:
            log.info("Page function %r returned None.", self.function)
            return

        output_path = os.path.join(config["output"], self.target)
        if not phial.utils.is_path_under_directory(output_path, config["output"]):
            phial.utils.log_and_die(
                "Page's target path must be relative and under the output directory. Did you "
                "begin the path with a / or .. ?")

        try:
            os.makedirs(os.path.join(config["output"], os.path.dirname(output_path)))
        except OSError:
            log.debug("Ignoring error making directory for %r.", output_path, exc_info=True)

        logging.info("Writing output of page function %r to %r.", self.function, self.target)

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
        bound_args = ", ".join([self.function.__name__] + list(repr(i) for i in self.args) +
                               ["{!s}={!r}".format(k, v) for k, v in self.kwargs.iteritems()])
        return "PartialFunction({})".format(bound_args)

    def __call__(self, *args, **kwargs):
        computed_kwargs = dict(self.kwargs.items() + kwargs.items())
        return self.function(*(self.args + args), **(computed_kwargs))


class BuildMultiplePagesCommand(phial.commands.Command):
    def __init__(self, function, target, foreach, preformat):
        self.function = function
        self.target = target
        self.foreach = foreach
        self.preformat = preformat

    def run(self, config):
        if isinstance(self.foreach, basestring):
            foreach = glob.iglob(self.foreach)
        else:
            foreach = self.foreach

        for i in foreach:
            preformatted = self.preformat(i)

            try:
                resolved_target = self.target.format(preformatted)
            except Exception as e:
                phial.utils.log_and_die(
                    "%s raised resolving target path %r for page function %r (item = %r)",
                    e.__class__.__name__, self.target, self.function, i, exc_info=True)

            bound_func = PartialFunction(self.function, resolved_target, i)
            BuildPageCommand(function=bound_func, target=resolved_target).run(config)
