# stdlib
import logging
import imp
import sys
import hashlib
import os
import stat
import time
import itertools
import glob
import multiprocessing
import BaseHTTPServer
import SimpleHTTPServer
from optparse import OptionParser, make_option

# internal
from . import processor

log = logging.getLogger("phial.tool")

def parse_arguments(args = sys.argv[1:]):
    option_list = [
        make_option(
            "-v", "--verbose", action = "store_true", default = False,
            help = "If specified, DEBUG messages will be printed."
        ),
        make_option(
            "-o", "--output", action = "store", default = "./output",
            help =
                "The directory to build the site into (it will be created if "
                "it does not exist). Defaults to %default."
        ),
        make_option(
            "-s", "--source", action = "store", default = "./site",
            help =
                "The directory the source files are in. Defaults to %default."
        ),
        make_option(
            "-m", "--monitor", action = "store_true", default = False,
            help =
                "If specified, the site will be rebuilt every time a change "
                "is made to a file or directory in the watch list."
        ),
        make_option(
            "-w", "--watch", action = "append", dest = "watch_list",
            default = [],
            help =
                "Adds a file or directory to the watch list. The path "
                "provided will be globbed every time the list is checked. By "
                "default, the watch list will be populated with the source "
                "directory as well as all of the unhidden files and "
                "directories in the app script's directory. This default "
                "behavior can be disabled with --no-watch-defaults."
        ),
        make_option(
            "--no-watch-defaults", action = "store_false", default = True,
            dest = "watch_defaults",
            help = "Do not populate the watch list with the default items"
        ),
        make_option(
            "--watch-poll-frequency", action = "store", default = "1",
            help =
                "The amount of time to wait in between polling for changes. "
                "Measured in seconds (can be a floating point value). "
                "Defaults to %default."
        ),
        make_option(
            "--serve", action = "store_true", default = False,
            help =
                "If sepcified, the built site will be served by a built-in "
                "HTTP server."
        ),
        make_option(
            "--serve-port", action = "store", default = "9000",
            help = "The TCP port to serve requests on. Defaults to %default."
        ),
        make_option(
            "--serve-host", action = "store", default = "localhost",
            help =
                "The host to serve requests on. This will determine the "
                "network device that is listened to. You almost certainly "
                "want to leave this on the default setting as exposing the "
                "server publicly using the built-in HTTP server could cause "
                "a security issue. Defaults to %default."
        )
    ]

    parser = OptionParser(
        usage = "usage: %prog [options] app",
        description = "Builds a Phial site.",
        option_list = option_list
    )

    options, args = parser.parse_args(args)

    if len(args) < 1:
        parser.error("You must specify the application file.")
    elif len(args) > 1:
        parser.error("Too many arguments!")

    return (options, args)

def setup_logging(verbose):
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    format = "[%(levelname)s] %(message)s"

    logging.basicConfig(level = log_level, format = format)

def get_state_token(dir_paths):
    """
    This function will iterate through the names and timestamps on every file
    in the given directories and return a unique hash of that information.

    If you take a token returned by this function and compare it to a token of
    the same directories, they will only be different if a file was added or
    removed, a file was updated, a file was renamed, or a directory was
    added/removed/renamed.

    """

    def expand_globs(paths):
        """Globs every path in paths and returns the resulting list."""

        # This will turn [[1, 2], [1]] into [1, 2, 1] (flatten the list)
        return itertools.chain.from_iterable(glob.glob(i)for i in paths)

    def walk_many(paths):
        """Generator that walks all the paths given."""

        for i in paths:
            for j in os.walk(i, topdown = True):
                yield j

    hasher = hashlib.md5()
    globbed_paths = list(expand_globs(dir_paths))
    for root, dirs, files in walk_many(globbed_paths):
        # Setting topdown to True above allows us to modify the directory list
        # in dirs. The walk function will visit each item in the order in which
        # they appear in that list. So here we sort it to make sure that the
        # order in which they are visited is well defined.
        dirs.sort()

        # Create a list of the directory's absolute paths (this is a list
        # comprehension below if you are unfamiliar with the construct).
        absolute_dirs = [os.path.join(root, i) for i in dirs]

        # Get a hash of that list (note that in Python you cannot take a hash
        # of a list because it is mutable so we first convert the list to a
        # tuple).
        dirs_hash = hash(tuple(absolute_dirs))

        # Add that hash into our final hash (after converting it to a string
        # because it was an integer before).
        hasher.update(str(dirs_hash))

        # Iterate through all the files in sorted order (so we always visit
        # them in the same order between different runs of this function).
        for i in sorted(files):
            # Get the absolute path of the file
            cur_file_path = os.path.join(root, i)

            # Add the aboslute path of the file to the final hash
            hasher.update(cur_file_path)

            # Add the last modified time of the file to the final hash
            hasher.update(str(os.stat(cur_file_path).st_mtime))

    return hasher.digest()

def monitor(watch_list, wait_time, callback):
    """
    Loops forever and runs callback whenever a change is detected in the watch
    list.

    """

    log.info("Entering monitor mode. Watch list: %r.", watch_list)

    while True:
        token = get_state_token(watch_list)

        while token == get_state_token(watch_list):
            time.sleep(wait_time)

        callback()

def build_app(app_path, source_dir, output_dir):
    """
    Builds the app. Will import the application in the current process so the
    forking verision of this function is probably what you want.

    """

    # Try and import the user's application
    try:
        userapp = imp.load_source("userapp", app_path)
    except:
        log.error("Could not load app at %r.", app_path, exc_info = True)
        sys.exit(100)

    try:
        log.info("Building application from sources in %r to output "
            "directory %r.", source_dir, output_dir)
        processor.process(source_dir = source_dir,
            output_dir = output_dir)
    except:
        log.warning("Failed to build app.", exc_info = True)

def fork_and_build_app(*args, **kwargs):
    """
    Forks a new process and builds the app.

    """

    p = multiprocessing.Process(target = build_app, args = args,
        kwargs = kwargs)

    # This will make sure Python tries to kill the process when it comes down
    # in case anything goes wrong.
    p.daemon = True

    log.debug("Forking to build app. Passings args %r and kwargs %r to "
        "build_app().", args, kwargs)
    p.start()

    # Wait for the process to terminate
    p.join()

    log.debug("Forked process finished, exit code %r.", p.exitcode)
    if p.exitcode != 0:
        log.warning("Failed to build site.")

class SimpleServer(object):
    def __init__(self, public_dir, host, port):
        self.public_dir = public_dir
        self.host = host
        self.port = port

        # The forked process actually serving.
        self._process = None

def fork_and_serve(public_dir, host, port, verbose):
    # Override the request handler's logging feature to log debug messages
    class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def log_message(self, *args, **kwargs):
            log.debug(*args, **kwargs)

    def serve():
        os.chdir(public_dir)
        server = BaseHTTPServer.HTTPServer((host, port), RequestHandler)
        server.log_message = log.debug
        server.serve_forever()

    log.debug("Starting server on host %r port %r.", host, port)
    p = multiprocessing.Process(target = serve)
    p.daemon = True
    p.start()

def main():
    try:
        _main()
    except KeyboardInterrupt:
        log.info("User sent interrupt, exiting.", exc_info = True)
        sys.exit(1)

def _main():
    options, arguments = parse_arguments()
    app_path = arguments[0]

    setup_logging(options.verbose)

    log.debug("Parsed command line arguments. arguments = %r, options = %r.",
        arguments, vars(options))

    watch_list = list(options.watch_list)
    if options.watch_defaults:
        # Add the directory of the application. If the user provided a path
        # like `app.py` dirname will give us an empty string, so translate that
        # into the current directory.
        app_dir = os.path.dirname(app_path)
        if not app_dir:
            app_dir = "."
        watch_list.append(app_dir)

        watch_list.append(options.source)

    # We'll pass this callback function to our monitor routine
    callback = lambda: fork_and_build_app(app_path, options.source,
        options.output)

    # Build the app before we go into monitor mode, also takes care of building
    # it if we're not going into monitor mode at all.
    callback()

    if options.serve:
        fork_and_serve(options.output, options.serve_host,
            int(options.serve_port), options.verbose)

    if options.monitor:
        monitor(watch_list, float(options.watch_poll_frequency), callback)
