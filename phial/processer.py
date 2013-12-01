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
import exceptions
import pages

# stdlib
import glob

# set up logging
import logging
log = logging.getLogger("phial.processor")

def process():
    # Go through every page we know about and process each one.
    for i in pages.get_pages():
        process_page(i)

def process_page(page):
    log.info("Processing %s", repr(page))

    # Check if this page is generated based on some files.
    if page.files is None:
        render_page(page)
    else:
        for f in glob_files(page.kwargs["files"]]):
            render_page(page, from_file = f)

def glob_files(files):
    """
    Returns a list of files matching the pattern(s) in ``files``.

    :param files: May be either a string or a list of strings. If a string, the
        pattern will be globbed and all matching files will be returned. If a
        list of strings, all of the patterns will be globbed and all unique
        file paths will be returned.

    :returns: A list of file paths.

    """

    if isinstance(files, basestring):
        result = glob.glob(files)
    else:
        # Glob every pattern and grab the unique results
        result_set = set()
        for i in files:
            result_set.update(glob.glob(i))
        result = list(result_set)

    return files
