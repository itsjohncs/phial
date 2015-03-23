# stdlib
from optparse import OptionParser, OptionGroup, Option
import BaseHTTPServer
import glob
import hashlib
import imp
import itertools
import logging
import multiprocessing
import os
import shutil
import SimpleHTTPServer
import sys
import time
import tempfile

# internal
from . import tasks
from . import loggers
from . import utils

log = loggers.get_logger(__name__)


def parse_arguments(args=sys.argv[1:]):
    class CustomOption(Option):
        TYPES = Option.TYPES + ("path", )
        TYPE_CHECKER = Option.TYPE_CHECKER
        TYPE_CHECKER["path"] = lambda option, opt, value: os.path.abspath(value)

    parser = OptionParser(
        usage="usage: %prog [options] app", option_class=CustomOption,
        description="The Phial command line tool. See http://github.com/brownhead/phial for more "
                    "information on the project."
    )

    parser.add_option(
        "-o", "--output", action="store", default="./output", metavar="PATH", type="path",
        help="The directory to build the site into (it will be created if it does not exist). "
             "The special value :temp: may be provided, in which case a temporary directory "
             "will be used (but is destroyed when Phial exits). Defaults to %default."
    )
    parser.add_option(
        "-e", "--output-encoding", action="store", default="utf_8",
        help="The encoding to use when writing unicode strings to the filesystem. Defaults to "
             "%default."
    )
    parser.add_option(
        "-v", "--verbose", action="count", default=0,
        help="Raises the verbosity. -v enables info level messages, -vv enables debug level "
             "messages. By default, only errors and warnings are displayed."
    )

    # optparse doesn't have native support for aliases so we use a callback here.
    def testing_callback(option, opt, value, parser):
        parser.values.output = ":temp:"
        parser.values.serve = True
        parser.values.monitor = True
    parser.add_option(
        "-t", "--testing", action="callback", callback=testing_callback,
        help="Alias for: '--output :temp: --serve --monitor'."
    )

    monitor_options = OptionGroup(
        parser, "Monitor Mode Options",
        "Phial can monitor a set of files for you and trigger a build every time one of the files "
        "is updated. This can be very useful when editing your site. These options control the "
        "details of this mode."
    )
    parser.add_option_group(monitor_options)
    monitor_options.add_option(
        "-m", "--monitor", action="store_true", default=False,
        help="If specified, the site will be rebuilt every time a change is made to a file or "
             "directory in the watch list."
    )
    monitor_options.add_option(
        "-w", "--watch", action="append", dest="watch_list", metavar="PATH", type="path",
        default=[],
        help="Adds a file or directory to the watch list. The path provided will be globbed "
             "every time the list is checked. By default, the watch list will be populated with "
             "tall of the unhidden files and directories in the app script's directory. This "
             "default behavior can be disabled with --no-watch-defaults."
    )
    monitor_options.add_option(
        "-W", "--dont-watch", action="append", dest="dont_watch_list", metavar="PATH", type="path",
        default=[],
        help="Adds a file or directory to the don't-watch list. The path provided will be "
             "globbed every time the list is checked. If a file or directory exists in both the "
             "watch list and the don't-watch list, it will not be watched. By default, the "
             "output directory will be in the don't-watch list. This default behavior can be "
             "disabled with --no-watch-defaults. This option exists because if your site "
             "generates some files into a directory in the watch list Phial can get caught in a "
             "loop where it will continually build your site over and over again."
    )
    monitor_options.add_option(
        "--no-watch-defaults", action="store_false", default=True, dest="watch_defaults",
        help="Do not populate the watch list or the don't-watch list with the default items."
    )
    monitor_options.add_option(
        "--watch-poll-frequency", action="store", default="1",
        help="The amount of time to wait in between polling for changes. Measured in seconds (can "
             "be a non-integer like 2.4, irrational numbers are not allowed). Defaults to "
             "%default."
    )

    server_options = OptionGroup(
        parser, "Serve Mode Options",
        "Phial can serve your site on your local system. Enabling serve mode is very similar to "
        "running `python -m SimpleHTTPServer` in the output directory."
    )
    parser.add_option_group(server_options)
    server_options.add_option(
        "--serve", action="store_true", default=False,
        help="If specified, the built site will be served by a built-in HTTP server."
    )
    server_options.add_option(
        "--serve-port", action="store", default="9000", metavar="PORT",
        help="The TCP port to serve requests on. Defaults to %default."
    )
    server_options.add_option(
        "--serve-host", action="store", default="localhost", metavar="HOST",
        help="The host to serve requests on. This will determine the network device that is "
             "listened to. You almost certainly want to leave this on the default setting as "
             "exposing the built-in HTTP server to the outside world could cause a security "
             "issue. Defaults to %default."
    )

    index_options = OptionGroup(
        parser, "Phial Index Options",
        "Phial will automatically delete any old files from the output directory. It needs to "
        "know which files it created in order to do that without destroying any other important "
        "files though. It does this by storing an index file. These options control the creation "
        "of that index file."
    )
    parser.add_option_group(index_options)
    index_options.add_option(
        "--index-path", action="store", default=".phial_index", dest="index_path", metavar="PATH",
        type="path",
        help="Where to store the index file. This is a path relative to the output directory "
             "(though it can also be an absolute path outside of it). Defaults to %default."
    )
    index_options.add_option(
        "--no-index", action="store_const", const=None, dest="index_path",
        help="If specified, no index file will be created and Phial will not clean the output "
             "directory."
    )

    options, args = parser.parse_args(args)

    if len(args) < 1:
        parser.error("You must specify the application file.")
    elif len(args) > 1:
        parser.error("Too many arguments!")

    return (options, args)


def setup_logging(verbose):
    if verbose >= 2:
        log_level = logging.DEBUG
    elif verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    phial_logger = logging.getLogger("phial")
    phial_logger.setLevel(log_level)

    handler = logging.StreamHandler()
    handler.setFormatter(loggers.DifferentFormatter())
    phial_logger.addHandler(handler)

    # We have to wait for the logger to be initialized to log this
    if verbose > 2:
        logging.warning("`-v` or `--verbose` specified more than 2 times.")


def get_state_token(dir_paths, exceptions):
    """Return unique hash of names and timestamps in the given directories.

    This function will iterate through the names and timestamps on every file
    in the given directories and return a unique hash of that information.

    If you take a token returned by this function and compare it to a token of
    the same directories, they will only be different if a file was added or
    removed, a file was updated, a file was renamed, or a directory was
    added/removed/renamed.

    Any item that exists in the exceptions list will be ignored. The format of
    the exceptions list is the same as for dir_paths.
    """
    def expand_globs(paths):
        """Glob every path in paths and returns the resulting list."""
        # This will turn [[1, 2], [1]] into [1, 2, 1] (flatten the list)
        return itertools.chain.from_iterable(glob.glob(i)for i in paths)

    def walk_many(paths):
        """Generator that walks all the paths given."""
        for i in paths:
            for j in os.walk(i, topdown=True):
                yield j

    def prune_paths(paths, exceptions_set, root="."):
        return [i for i in paths if os.path.abspath(os.path.join(root, i)) not in exceptions_set]

    # Glob and get a canonical path for each of the exceptions
    exceptions = expand_globs(exceptions)
    exceptions = set(os.path.abspath(i) for i in exceptions)

    # Prune the directory list of any exceptions
    dir_paths = prune_paths(dir_paths, exceptions)

    # Glob all the paths in the directory list
    globbed_paths = expand_globs(dir_paths)

    hasher = hashlib.md5()
    for root, dirs, files in walk_many(globbed_paths):
        # Setting topdown to True above allows us to modify the directory list
        # in dirs. The walk function will visit each item in the order in which
        # they appear in that list. So here we sort it to make sure that the
        # order in which they are visited is well defined, we also make sure
        # that none of the directories are in our exceptions list or hidden.
        # Note that we need to do slice assignment to ensure that we're
        # affecting the original list.
        dirs[:] = prune_paths(dirs, exceptions, root)
        dirs[:] = [i for i in dirs if not i.startswith(".")]
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
        for i in sorted(prune_paths(files, exceptions)):
            # Get the absolute path of the file
            cur_file_path = os.path.join(root, i)

            # Add the aboslute path of the file to the final hash
            hasher.update(cur_file_path)

            # Add the last modified time of the file to the final hash
            hasher.update(str(os.stat(cur_file_path).st_mtime))

    return hasher.digest()


def monitor(watch_list, dont_watch_list, wait_time, callback):
    """Loop forever and run callback whenever a change is detected in the watch list."""
    log.info("Entering monitor mode. Watch list: {0!r}. Don't watch list: {1!r}.", watch_list,
             dont_watch_list)

    old_token = get_state_token(watch_list, dont_watch_list)

    while True:
        while True:
            time.sleep(wait_time)

            current_token = get_state_token(watch_list, dont_watch_list)
            if old_token != current_token:
                break
        old_token = current_token

        log.info("Detected change in source files, rebuilding...")

        callback()


def build_app(app_path, options):
    """Build the app.

    Will import the application in the current process so the foring version of this function is
    probably what you want.
    """
    app_dir = os.path.dirname(app_path)
    os.chdir(app_dir)

    # Try and import the user's application
    try:
        # If we don't use the absolute path when importing we may not get
        # proper tracebacks if the current directory changes.
        assert os.path.isabs(app_path)

        imp.load_source("userapp", app_path)
    except:
        log.error("Could not load app at {0}.", app_path, exc_info=True)
        sys.exit(100)

    try:
        log.info("Building application from sources in {0} to output directory {1}.",
                 app_dir, options.output)

        try:
            utils.makedirs(options.output)
        except OSError:
            log.debug("Ignoring error creating output directory at {0}.", options.output,
                      exc_info=True, exc_ignored=True)

        log.debug("About to consume queue: {0!r}", list(tasks.global_queue))
        for i in tasks.global_queue:
            i.run(vars(options))
    except Exception as e:
        show_tb = not isinstance(e, loggers.FatalError)
        log.warning("Failed to build app.", exc_info=show_tb)


def fork_and_build_app(*args, **kwargs):
    """Fork a new process and builds the app."""
    p = multiprocessing.Process(target=build_app, args=args, kwargs=kwargs)

    # This will make sure Python tries to kill the process when it comes down
    # in case anything goes wrong.
    p.daemon = True

    log.debug("Forking to build app. Passings args {0!r} and kwargs {1!r} to build_app().", args,
              kwargs)
    p.start()

    # Wait for the process to terminate
    p.join()

    log.debug("Forked process finished, exit code {0!s}.", p.exitcode)
    if p.exitcode != 0:
        log.warning("Failed to build site.")


def fork_and_serve(public_dir, host, port, verbose):
    # Override the request handler's logging feature to log debug messages
    class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def log_message(self, *args, **kwargs):
            log.debug(*args, **kwargs)

    def serve():
        try:
            sys.stdout = open(os.devnull, "w")
            sys.stderr = open(os.devnull, "w")

            os.chdir(public_dir)
            server = BaseHTTPServer.HTTPServer((host, port), RequestHandler)
            server.serve_forever()
        except KeyboardInterrupt:
            pass

    # Print to stdout to ensure the user always recieves this message (without
    # doing anything too clunky like logging an error).
    print "Serving site at http://{0}:{1}".format(host, port)
    p = multiprocessing.Process(target=serve)
    p.daemon = True
    p.start()


def main(args=sys.argv[1:]):
    options, arguments = parse_arguments(args)

    deletion_list = []

    try:
        _main(options, arguments, deletion_list)
    except KeyboardInterrupt:
        log.info("User sent interrupt, exiting.", exc_info=options.verbose, exc_ignored=True)
        sys.exit(1)
    finally:
        if deletion_list:
            log.debug("Removing files/directories {0!r}.", deletion_list)
            for i in deletion_list:
                shutil.rmtree(i)


def run_tool(*args):
    """Run the Phial command line tool with the given arguments."""
    main(list(args))


# NOTE(brownhead): The noqa here is because the complexity of this function is too high. I think
#     this is appropriate for the sort of thing this function is doing though, so going to ignore
#     it for now. Not against splitting this function up in the future though!
def _main(options, arguments, deletion_list):  # noqa
    app_path = os.path.abspath(arguments[0])

    setup_logging(options.verbose)

    log.debug("Parsed command line arguments. arguments = {0!r}, options = {1!r}.", arguments,
              vars(options))

    if options.output == ":temp:":
        temp_dir = tempfile.mkdtemp()
        deletion_list.append(temp_dir)
        log.info("Created temporary directory at {0}.", temp_dir)
        options.output = temp_dir

    watch_list = list(options.watch_list)
    dont_watch_list = list(options.dont_watch_list)
    if options.watch_defaults:
        # Add the directory of the application. If the user provided a path
        # like `app.py` dirname will give us an empty string, so translate that
        # into the current directory.
        app_dir = os.path.dirname(app_path)
        if not app_dir:
            app_dir = "."
        watch_list.append(app_dir)

        dont_watch_list.append(options.output)

    # We'll pass this callback function to our monitor routine
    def callback():
        fork_and_build_app(app_path, options)

    # Build the app before we go into monitor mode, also takes care of building
    # it if we're not going into monitor mode at all.
    callback()

    if options.serve:
        # This will fork off a web server and return immediately
        fork_and_serve(options.output, options.serve_host, int(options.serve_port),
                       options.verbose)

    if options.monitor:
        # This function never returns
        monitor(watch_list, dont_watch_list, float(options.watch_poll_frequency), callback)

    # If the user wants to serve the site but didn't enable monitoring we'd
    # exit immediately if we didn't do this.
    if options.serve:
        # Sleep forever (until keybaord interrupt)
        log.debug("Sleeping forever.")
        while True:
            time.sleep(1)
