# stdlib
import StringIO
import traceback
import sys
import logging
import string
import re


class DifferentFormatter(object):
    class _ColoredStringFormatter(string.Formatter):
        ZERO_LENGTH_RE = re.compile(r"(?P<open_braces>{+)}")

        def __init__(self, colorizer):
            self.colorizer = colorizer
            self.count = 0

        def convert_field(self, value, conversion):
            converted = string.Formatter.convert_field(self, value, conversion)
            return self.colorizer(converted)

        def parse(self, format_string):
            # This is a list so I can access it inside the function
            count = [0]

            def repl(match):
                # If there is an odd number of open braces, then we know this is a zero-length
                # field.
                if len(match.group("open_braces")) % 2 == 1:
                    r = match.group("open_braces") + str(count[0]) + "}"
                    count[0] += 1
                    return r
                else:
                    return match.group(0)

            # Replace any zero length field with a numbered field as appropriate than pass it off
            # to the parser.
            converted = self.ZERO_LENGTH_RE.sub(repl, format_string)
            return string.Formatter.parse(self, converted)


    DEFAULT_STYLESHEET = {
        "default": [],
        "critical": [1, 31],  # bold red
        "error": [31],  # red
        "warning": [33],  # yellow
        "info": [],  # default
        "debug": [2],  # faint
        "argument": [34],  # blue
        "ignored_tb": [2],  # faint
        "tb_path": [34],  # blue
        "tb_lineno": [34],  # blue
        "tb_exc_name": [31],  # red
    }

    def __init__(self, stylesheet=None):
        self.stylesheet = self.DEFAULT_STYLESHEET.copy()
        if stylesheet is not None:
            self.stylesheet.update(stylesheet)

    @staticmethod
    def style_text(stylesheet, styles, base_styles, text):
        # Form up the sequences we'll use to color the text.
        ansify = lambda codes: u"\x1B[" + u";".join(map(str, [0] + codes)) + u"m"
        prefix = ansify(sum([stylesheet[i] for i in base_styles + styles], []))
        postfix = ansify(sum([stylesheet[i] for i in base_styles], []))

        return prefix + text + postfix

    def format(self, record):
        shortname = record.name
        if shortname.startswith("phial."):
            shortname = shortname[len("phial"):]

        formatter = self._ColoredStringFormatter(
            lambda arg: self.style_text(self.stylesheet, ["argument"], [record.levelname.lower()],
                                        arg))
        message = formatter.format(record.msg, *record.args)

        formatted = u"[{record.name}:{record.lineno}] {message}".format(record=record,
                                                                        message=message)
        formatted = self.style_text(self.stylesheet, [record.levelname.lower()], [], formatted)

        tb = self.format_traceback(record)
        if tb:
            formatted += u"\n" + tb

        return formatted

    @staticmethod
    def indent_text(text):
        lines = text.split("\n")
        processed = []
        for i in lines:
            processed.append("... " + i)

        return "\n".join(processed)

    def format_traceback(self, record):
        if not record.exc_info:
            return None

        dummy_file = StringIO.StringIO()
        traceback.print_exception(record.exc_info[0], record.exc_info[1], record.exc_info[2],
                                  file=dummy_file)
        tb = dummy_file.getvalue().strip()

        classnames = [record.levelname.lower()]
        if getattr(record, "exc_ignored", False):
            classnames.append("ignored_tb")

        tb = self.highlight_tb(tb, classnames)

        tb = self.indent_text(tb)

        return self.style_text(self.stylesheet, classnames, [], tb)

    def highlight_tb(self, tb, base_classnames):
        FILE_LINE_RE = re.compile(r'^  File (".+"), line ([0-9]+), in (.*)$',
                                  re.MULTILINE | re.UNICODE)
        def repl_file_line(match):
            return '  File {0}, line {1}, in {2}'.format(
                self.style_text(self.stylesheet, ["tb_path"], base_classnames, match.group(1)),
                self.style_text(self.stylesheet, ["tb_lineno"], base_classnames, match.group(2)),
                match.group(3)
            )

        FOOTER_LINE_RE = re.compile(r"^(\w+)(.*)$", re.MULTILINE | re.UNICODE)
        def repl_footer_line(match):
            return self.style_text(self.stylesheet, ["tb_exc_name"], base_classnames, 
                                   match.group(1)) + match.group(2)

        lines = tb.split("\n")
        if len(lines) < 2:
            return tb
        lines[-1] = FOOTER_LINE_RE.sub(repl_footer_line, lines[-1])
        tb = "\n".join(lines)

        tb = FILE_LINE_RE.sub(repl_file_line, tb)

        return tb


class FatalError(SystemExit, Exception):
    pass


class Logger(object):
    def __init__(self, logger):
        self.logger = logger

    def fatal(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
        raise FatalError()

    def log(self, lvl, msg, *args, **kwargs):
        extra = kwargs.pop("extra", {})
        extra["exc_ignored"] = kwargs.pop("exc_ignored", False)

        return self.logger.log(lvl, msg, *args, extra=extra, **kwargs)

    def error(self, msg, *args, **kwargs):
        return self.log(logging.ERROR, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return self.log(logging.WARNING, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return self.log(logging.INFO, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        return self.log(logging.DEBUG, msg, *args, **kwargs)


def get_logger(name):
    return Logger(logging.getLogger(name))
