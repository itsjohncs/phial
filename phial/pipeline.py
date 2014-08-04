__all__ = ("pipeline", "concat", "cout", )

# stdlib
import shutil
import sys
import glob
import os.path

# internal
import phial.utils
import phial.commands
import phial.documents

# set up logging
import phial.loggers
log = phial.loggers.get_logger(__name__)


def pipeline(foreach, command_queue=phial.commands.global_queue):
    def real_decorator(function):
        command_queue.enqueue(BuildPipelineCommand(function, foreach))
        return function

    return real_decorator


class BuildPipelineCommand(phial.commands.Command):
    def __init__(self, function, foreach):
        self.function = function
        self.foreach = foreach

    def run(self, config):
        if isinstance(self.foreach, basestring):
            foreach = [phial.documents.open_file(i) for i in glob.iglob(self.foreach)]
        else:
            foreach = self.foreach

        result = self.function(PipelineSource(foreach))
        log.info("Pipe function {0!r} yielded {1!s} files.", self.function, len(result.contents))

        for i in result.contents:
            output_path = os.path.join(config["output"], i.name)
            if not phial.utils.is_path_under_directory(output_path, config["output"]):
                log.die(
                    "Target path must be relative and under the output directory. Did you begin "
                    "the path with a / or .. ?")

            shutil.copyfileobj(i, phial.documents.unicodify_file_object(open(output_path, "w")))


class PipelineSource(object):
    def prepare_contents(self):
        for i in self.contents:
            assert hasattr(i, "name"), "{0!r} does not have name attribute.".format(i)
            i.seek(0)

    def __init__(self, contents):
        self.contents = contents
        self.prepare_contents()

    def pipe(self, transform):
        self.contents = transform(self.contents)
        self.prepare_contents()
        return self

    def __or__(self, transform):
        return self.pipe(transform)

    def __repr__(self):
        return self.__class__.__name__ + "(" + repr(self.contents) + ")"


class concat(object):
    def __init__(self, output_name=None):
        self.output_name = output_name

    def __call__(self, contents):
        result = phial.utils.TemporaryFile(name=self.output_name)
        for i in contents:
            shutil.copyfileobj(i, result)
        return [result]


class cout(object):
    def __init__(self, out=sys.stdout):
        self.out = sys.stdout

    def __call__(self, contents):
        for i in contents:
            shutil.copyfileobj(i, self.out)
        return contents
