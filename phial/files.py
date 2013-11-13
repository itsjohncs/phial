_FRONT_MATTER_MARKER = u"---"
"""The string that denotes the beginning and end of YAML front matter."""

class File:
    """
    A Phial file.
    """

    def __init__(self, path):
        self.path = path

    def _parse_frontmatter(self):
        """
        Will consume and parse any front matter present in the file. Returns a
        dictionary of template fields that were specified in the front matter
        or `None` if no front matter is present.

        """

        with open(self.path) as f:
            # Check to see if there is YAML front matter
            first_line = unicode(f.readline()).rstrip()
            if first_line == _FRONT_MATTER_MARKER:
                # Iterate through every line until we hit the end of the front
                # matter.
                import StringIO
                front_matter = StringIO.StringIO()
                for line in f:
                    uline = unicode(line)
                    if uline.rstrip() == _FRONT_MATTER_MARKER:
                        break
                    else:
                        front_matter.write(uline)
                else:
                    # This occurs if we didn't break above, so we know that
                    # there was no end to the front matter. This is illegal.
                    raise exceptions.BadFrontMatter(
                        path = self.path,
                        error_string = "No end of front matter."
                    )

                front_matter.flush()
                front_matter.seek(0)



                # TODO: Do something with the front matter(parse it)
                return front_matter.getvalue()

        return None

    def __getitem__(self, attribute):
        return self.attributes[attribute]

    def __contains__(self, attribute):
        return attribute in self.attributes
