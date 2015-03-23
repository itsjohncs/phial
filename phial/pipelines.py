# stdlib
import shutil
import sys
import os.path
import subprocess

# internal
from . import utils
from . import tasks
from . import documents

# set up logging
import phial.loggers
log = phial.loggers.get_logger(__name__)


@utils.public
def pipeline(foreach=[], binary_mode=True, task_queue=tasks.global_queue, depends_on=None):
    def real_decorator(function):
        task_queue.enqueue(PipelineTask(function, foreach, binary_mode, function, depends_on))
        return function

    return real_decorator


class PipelineTask(tasks.Task):
    def __init__(self, function, foreach, binary_mode, id, depends_on=None):
        self.function = function
        self.foreach = foreach
        self.binary_mode = binary_mode
        self.id = id
        self.files = None
        self.depends_on = depends_on

    def run(self, config):
        if self.binary_mode:
            def open_file(path):
                return open(path, "rb")
        else:
            open_file = documents.open_file

        # Glob and open all of the files the user specified
        globbed_foreach = utils.glob_foreach_list(self.foreach)
        files = [open_file(path) for path in globbed_foreach]

        result = self.function(PipelineSource(files))
        log.info("Pipe function {0!r} yielded {1!s} files.", self.function, len(result.contents))

        self.files = list(result.contents)
        for i in self.files:
            output_path = os.path.join(config["output"], i.name)
            if not utils.is_path_under_directory(output_path, config["output"]):
                log.fatal(
                    "Target path must be relative and under the output directory. Did you begin "
                    "the path with a / or .. ?")

            # Ensure that the target directory exists
            utils.makedirs(os.path.dirname(output_path))

            if self.binary_mode:
                output_file = open(output_path, "wb")
            else:
                output_file = documents.unicodify_file_object(open(output_path, "w"))

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

        result = utils.TemporaryFile(name=self.output_name)
        result.write(stdout)
        return [result]


@utils.public
class concat(object):
    def __init__(self, output_name=None):
        self.output_name = output_name

    def __call__(self, contents):
        result = utils.TemporaryFile(name=self.output_name)
        for i in contents:
            shutil.copyfileobj(i, result)
        return [result]


@utils.public
class cout(object):
    def __init__(self, out=sys.stdout):
        self.out = sys.stdout

    def __call__(self, contents):
        for i in contents:
            shutil.copyfileobj(i, self.out)
        return contents


@utils.public
class move(object):
    def __init__(self, to):
        self.to = to

    def __call__(self, contents):
        for i in contents:
            i = os.path.join(self.to, i)
        return contents


@utils.public
class map(object):
    def __init__(self, func):
        self.func = func

    def __call__(self, contents):
        return [self.func(i) for i in contents]
