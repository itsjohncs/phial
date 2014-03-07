# stdlib
import logging
import imp
import sys
import hashlib
import os
import stat
import time
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
            "-w", "--watch", action = "store_true", default = False,
            help =
                "If specified, the site will be rebuilt every time a change "
                "is made to a file in the source directory."
        ),
        make_option(
            "--watch-poll-frequency", action = "store", default = "1",
            help =
                "The amount of time to wait in between polling for changes. "
                "Measured in seconds (can be a floating point value). "
                "Defaults to %default."
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

def get_state_token(dir_path):
    """
    This function will iterate through the names and timestamps on every file
    in the given directory and return a unique hash of that information.

    If you take a token returned by this function and compare it to a token of
    the same directories, they will only be different if a file was added or
    removed, a file was updated, a file was renamed, or a directory was
    added/removed/renamed.

    """

    hasher = hashlib.md5()
    for root, dirs, files in os.walk(dir_path, topdown = True):
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

def main():
    try:
        _main()
    except KeyboardInterrupt:
        log.info("User sent interrupt, exiting.", exc_info = True)
        sys.exit(1)

def _main():
    options, arguments = parse_arguments()

    setup_logging(options.verbose)

    log.debug("Parsed command line arguments. arguments = %r, options = %r.",
        arguments, vars(options))

    # Try and import the user's application
    app_path = arguments[0]
    try:
        userapp = imp.load_source("userapp", app_path)
    except:
        log.error("Could not load app at %r.", app_path, exc_info = True)
        sys.exit(100)

    if options.watch:
        while True:
            # This will hash the state of the source directory
            token = get_state_token(options.source)

            try:
                log.info("Building application from sources in %r to output "
                    "directory %r.", options.source, options.output)
                processor.process(src_dir = options.source,
                    output_dir = options.output)
            except:
                log.warning("Failed to build app, waiting for change to try "
                    "again.", exc_info = True)

            # Wait until the state of the source directory changes
            while token == get_state_token(options.source):
                time.sleep(float(options.watch_poll_frequency))
            log.info("Change detected in source directory %r.",
                options.source)
    else:
        try:
            processor.process(src_dir = options.source,
                    output_dir = options.output)
        except:
            log.error("Could not build app.", exc_info = True)
            sys.exit(101)

    log.info("Succesfully built application. Output in %r.", options.output)
