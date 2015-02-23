# stdlib
import shutil
import sys
import os.path
import subprocess

# internal
import phial.utils
import phial.commands
import phial.documents

# set up logging
import phial.loggers
log = phial.loggers.get_logger(__name__)


@phial.utils.public
def pipeline(foreach, binary_mode=True, command_queue=phial.commands.global_queue):
    def real_decorator(function):
        command_queue.enqueue(BuildPipelineCommand(function, foreach, binary_mode))
        return function

    return real_decorator


class BuildPipelineCommand(phial.commands.Command):
    def __init__(self, function, foreach, binary_mode):
        self.function = function
        self.foreach = foreach
        self.binary_mode = binary_mode

    def run(self, config):
        if self.binary_mode:
            def open_file(path):
                return open(path, "rb")
        else:
            open_file = phial.documents.open_file

        # Glob and open all of the files the user specified
        globbed_foreach = phial.utils.glob_foreach_list(self.foreach)
        files = [open_file(path) for path in globbed_foreach]

        result = self.function(PipelineSource(files))
        log.info("Pipe function {0!r} yielded {1!s} files.", self.function, len(result.contents))

        for i in result.contents:
            output_path = os.path.join(config["output"], i.name)
            if not phial.utils.is_path_under_directory(output_path, config["output"]):
                log.fatal(
                    "Target path must be relative and under the output directory. Did you begin "
                    "the path with a / or .. ?")

            # Ensure that the target directory exists
            phial.utils.makedirs(os.path.dirname(output_path))

            if self.binary_mode:
                output_file = open(output_path, "wb")
            else:
                output_file = phial.documents.unicodify_file_object(open(output_path, "w"))

            shutil.copyfileobj(i, output_file)


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


class run(object):
    def __init__(self, output_name, args, popen_kwargs=None):
        self.args = args
        self.output_name = output_name
        self.popen_kwargs = popen_kwargs or {}

    def __call__(self, contents):
        p = subprocess.Popen(self.args, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                             **self.popen_kwargs)
        stdout = p.communicate("".join(i.read() for i in contents))[0]

        result = phial.utils.TemporaryFile(name=self.output_name)
        result.write(stdout)
        return [result]


@phial.utils.public
class concat(object):
    def __init__(self, output_name=None):
        self.output_name = output_name

    def __call__(self, contents):
        result = phial.utils.TemporaryFile(name=self.output_name)
        for i in contents:
            shutil.copyfileobj(i, result)
        return [result]


@phial.utils.public
class cout(object):
    def __init__(self, out=sys.stdout):
        self.out = sys.stdout

    def __call__(self, contents):
        for i in contents:
            shutil.copyfileobj(i, self.out)
        return contents


@phial.utils.public
class move(object):
    def __init__(self, to):
        self.to = to

    def __call__(self, contents):
        for i in contents:
            i = os.path.join(self.to, i)
        return contents
