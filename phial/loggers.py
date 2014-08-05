# stdlib
import StringIO
import traceback
import sys
import logging
import string
import re


def style_text(classnames, text, base_classnames="default"):
    ansi = lambda values: u"\x1B[" + u";".join(unicode(i) for i in values) + u"m"
    STYLES = {
        "default": [0],
        "error": [31],  # red
        "warning": [33],  # yellow
        "info": [0],  # default
        "debug": [0, 2],  # faint default
        "argument": [34],  # blue
        "ignored_tb": [2],  # faint
        "tb_path": [34],  # blue
        "tb_lineno": [34],  # blue
        "tb_exc_name": [31],  # red
    }

    values = []
    for i in classnames.split():
        values += STYLES[i.lower()]

    base_values = []
    for i in base_classnames.split():
        base_values += STYLES[i.lower()]

    return ansi(values) + text + ansi(base_values)


class ColoredStringFormatter(string.Formatter):
    def __init__(self, base_classnames):
        self.base_classnames = base_classnames

    def convert_field(self, value, conversion):
        result = string.Formatter.convert_field(self, value, conversion)
        return style_text("argument", result, base_classnames=self.base_classnames)


class LogFormatter(object):
    def format(self, record):
        shortname = record.name
        if shortname.startswith("phial."):
            shortname = shortname[len("phial"):]

        message = ColoredStringFormatter(record.levelname).format(record.msg, *record.args)

        formatted = u"[{0}] {1}".format(shortname, message)
        formatted = style_text(record.levelname, formatted)

        tb = self.format_traceback(record)
        if tb:
            formatted += u"\n" + tb

        return style_text(record.levelname, formatted)

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

        classnames = record.levelname
        if getattr(record, "exc_ignored", False):
            classnames += " ignored_tb"

        tb = self.highlight_tb(tb, classnames)

        tb = self.indent_text(tb)

        return style_text(classnames, tb)

    @staticmethod
    def highlight_tb(tb, base_classnames):
        FILE_LINE_RE = re.compile(r'^  File (".+"), line ([0-9]+), in (.*)$', re.MULTILINE | re.UNICODE)
        def repl_file_line(match):
            return '  File {0}, line {1}, in {2}'.format(
                style_text("tb_path", match.group(1), base_classnames),
                style_text("tb_lineno", match.group(2), base_classnames),
                match.group(3)
            )

        FOOTER_LINE_RE = re.compile(r"^(\w+)(.*)$", re.MULTILINE | re.UNICODE)
        def repl_footer_line(match):
            return style_text("tb_exc_name", match.group(1), base_classnames) + match.group(2)

        lines = tb.split("\n")
        if len(lines) < 2:
            return tb
        lines[-1] = FOOTER_LINE_RE.sub(repl_footer_line, lines[-1])
        tb = "\n".join(lines)

        tb = FILE_LINE_RE.sub(repl_file_line, tb)

        return tb


class LoggedDeath(Exception):
    pass


class Logger(object):
    def __init__(self, logger):
        self.logger = logger

    def die(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
        raise LoggedDeath()

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
