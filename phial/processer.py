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

import exceptions

import logging
log = logging.getLogger("phial.renderer")

def process():
    import pages

    log.debug("Process called. _pages = %s", repr(pages._pages))

    # Go through every page we know about and process each one.
    for page in pages._pages:
        process_page(page)


def process_page(page):
    log.debug("Processing %s", repr(page))

    # Check if this page is generated based on some files.
    if "files" in page.kwargs:
        for f in glob_files(page.kwargs["files"]]):
            render_page(page, from_file = f)
    else:
        render_page(page)

def glob_files(page):
    import glob
    files = glob.glob(page.files)

    log.debug("Globbed %s and got %s", repr(page.files), repr(files))
