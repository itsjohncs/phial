__all__ = ("assets", )

# internal
import phial.commands
import phial.utils

# stdlib
import glob
import os.path
import shutil

# set up logging
import phial.loggers
log = phial.loggers.get_logger(__name__)


def assets(target, foreach, preformat=os.path.basename, command_queue=phial.commands.global_queue):
    command_queue.enqueue(CopyAssetsCommand(target, foreach, preformat))


class CopyAssetsCommand(phial.commands.Command):
    def __init__(self, target, foreach, preformat):
        self.target = target
        self.foreach = foreach
        self.preformat = preformat

    def run(self, config):
        if isinstance(self.foreach, basestring):
            foreach = glob.iglob(self.foreach)
        else:
            foreach = self.foreach

        for i in foreach:
            if not os.path.exists(i):
                log.fatal("Unknown file {0!s} given as source for asset.", i)

            preformatted = self.preformat(i)

            try:
                resolved_target = self.target.format(preformatted)
            except Exception:
                # TODO(brownhead): This log message could use some improvement.
                log.fatal("Could not resolve target path {0!s} for asset {1!s}", self.target,
                          i, exc_info=True)

            try:
                phial.utils.makedirs(
                    os.path.join(config["output"], os.path.dirname(resolved_target)))
            except OSError:
                log.debug("Ignoring error making directory for {0}.", resolved_target,
                          exc_info=True, exc_ignored=True)

            shutil.copy2(i, os.path.join(config["output"], resolved_target))
