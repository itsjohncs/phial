# Copyright (c) 2013 John Sullivan
# Copyright (c) 2013 Other contributers as noted in the CONTRIBUTERS file
#
# This file is part of Phial
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# internal
from . import exceptions
from . import pages
from . import documents
from . import utils

# stdlib
import os
import errno

# set up logging
import logging
log = logging.getLogger("phial.processor")

def _mkdirs(dir_path):
    """Creates a directory and its parents if they don't exist."""

    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def process(source_dir = "./site", output_dir = "./output"):
    # We want all of the relative paths in the user's code to be relative to
    # the source directory, so we're actually going to modify our current
    # directory process-wide.
    old_cwd = os.getcwd()
    os.chdir(source_dir)
    log.debug("Changed into source directory %r.", source_dir)

    # Go through every page we know about and process each one.
    rendered_pages = []
    for i in pages.get_pages():
        rendered_pages += process_page(i)

    # During the output step, we reset the current directory back to whatever
    # it was to begin with.
    os.chdir(old_cwd)

    # Spill out the rendered pages into the output directory
    for i in rendered_pages:
        destination = os.path.join(output_dir, i.path)
        if not os.path.abspath(destination).startswith(
                os.path.abspath(output_dir)):
            raise ValueError("destination path is invalid: {}".format(
                destination))

        # Make sure the destination's directory exists
        _mkdirs(os.path.dirname(destination))

        with open(destination, "w") as f:
            if isinstance(i.content, unicode):
                f.write(i.content.encode("utf_8"))
            else:
                f.write(i.content)

def process_page(page):
    """
    Processes a page and returns a list of RenderedPage objects.

    """

    # Check if this page is generated based on some files.
    rendered_pages = []
    if page.files is None:
        rendered_pages.append(page.render())
    else:
        for f in utils.glob_files(page.files):
            # Only open the file if we're supposed to
            if page.open_files:
                document = documents.Document(f)
            else:
                document = f

            rendered_pages.append(page.render(document))

    return rendered_pages
