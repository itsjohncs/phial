class BadFrontmatter(RuntimeError):
    """
    Raised when a document's frontmatter is invalid somehow.

    """

    def __init__(self, path = None, error_string = None, yaml_error = None):
        self.path = path
        self.error_string = error_string
        self.yaml_error = yaml_error

    def __str__(self):
        path = self.path or "<unknown>"
        error_string = self.error_string or "<Not Specified>"

        if self.yaml_error is None:
            return ("Bad frontmatter in '%s': %s" %
                (path, error_string))
        else:
            return ("Bad frontmatter in '%s': %s... YAML parser raised "
                "error: %s" % (path, error_string, self.yaml_error))

    def __repr__(self):
        return "%s(path = %s, error_string = %s, yaml_error = %s)" % (
            type(self).__name__, repr(self.path), repr(self.error_string),
            repr(self.yaml_error))

class BadPageFunction(RuntimeError):
    def __self__(self, message, page):
        self.message = message
        self.page = page

        RuntimeError.__init__(self, message)

    def get_string(self):
        return str(self)

    def __str__(self):
        return self.get_string()
