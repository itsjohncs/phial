# stdlib
import logging
import imp
import sys
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
            help = "The directory the source files are in."
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

def main():
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

    log.info("Building application from sources in %r.", options.source)
    try:
        processor.process(src_dir = options.source,
            output_dir = options.output)
    except:
        log.error("Failed to build app.", exc_info = True)
        sys.exit(101)

    log.info("Succesfully built application. Output in %r.", options.output)
