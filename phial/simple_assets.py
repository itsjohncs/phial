__all__ = ["simple_assets"]

# internal
import phial.commands

# stdlib
import glob

# set up logging
import logging
log = logging.getLogger(__name__)


def simple_assets(*args, **kwargs):
    command_queue = kwargs.pop("command_queue", phial.commands.global_queue)
    if kwargs:
        raise TypeError("Unknown keyword argument(s): " + ", ".join(kwargs.iterkeys()))

    command_queue.enqueue(CopySimpleAssetsCommand(args))


class CopySimpleAssetsCommand(phial.commands.Command):
    def __init__(self, paths):
        self.paths = paths

    def run(self, config):
        for path in self.paths:
            for i in glob.iglob(path):
                try:
                    os.makedirs(os.path.join(config["output"], os.path.dirname(i)))
                except OSError:
                    log.debug("Ignoring error making directory for %r.", i, exc_info=True)

                shutil.copy2(i, output)
