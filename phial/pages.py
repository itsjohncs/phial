# stdlib
import codecs
import os.path

# internal
import phial.commands
import phial.utils

# set up logging
import phial.loggers
log = phial.loggers.get_logger(__name__)


@phial.utils.public
def basename_noext(path):
    return os.path.splitext(os.path.basename(path))[0]


@phial.utils.public
def page(target, foreach=None, preformat=basename_noext,
         command_queue=phial.commands.global_queue):
    def real_decorator(function):
        command_queue.enqueue(BuildPageCommand(function, target, foreach, preformat))
        return function

    return real_decorator


class BuildPageCommand(phial.commands.Command):
    def __init__(self, function, target, foreach, preformat):
        self.function = function
        self.target = target
        self.foreach = foreach
        self.preformat = preformat

    def run(self, config):
        if self.foreach is None:
            self._write_page(config, self.function(), self.target)
            return

        foreach = phial.utils.glob_foreach_list(self.foreach)

        for i in foreach:
            preformatted = self.preformat(i)

            try:
                resolved_target = self.target.format(preformatted)
            except Exception:
                log.fatal("Could not resolve target path {0!r} for page function {1!r} "
                          "(item = {2!r})", self.target, self.function, i, exc_info=True)

            self._write_page(config, self.function(resolved_target, i), resolved_target)

    def _write_page(self, config, output, target):
        if output is None:
            # TODO(brownhead): Expose more useful information here.
            log.info("Page function returned None.")
            return

        output_path = os.path.join(config["output"], target)
        if not phial.utils.is_path_under_directory(output_path, config["output"]):
            log.fatal("Page's target path must be relative and under the output directory. Did "
                      "you begin the path with a / or .. ?")

        try:
            phial.utils.makedirs(os.path.join(config["output"], os.path.dirname(output_path)))
        except OSError:
            log.debug("Ignoring error making directory for {0}.", output_path, exc_info=True,
                      exc_ignored=True)

        # log.info("Writing output of page function {0!r} to {1}.", function, target)

        if isinstance(output, unicode):
            with codecs.open(output_path, "w", config["output_encoding"]) as f:
                f.write(output)
        elif isinstance(output, str):
            with open(output_path, "wb") as f:
                f.write(output)
        else:
            log.fatal("Page function must return str or unicode instance, got {0!r}.", output)
