# Copyright (c) 2013-2014 John Sullivan
# Copyright (c) 2013-2014 Other contributers as noted in the CONTRIBUTERS file
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
import shutil

# set up logging
import logging
log = logging.getLogger(__name__)

def _mkdirs(dir_path):
    """Creates a directory and its parents if they don't exist."""

    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def process(source_dir = "./site", output_dir = "./output"):
    """
    Processes all of the pages in your site appropriately. This is the function
    the drives the generation of a Phial site and is what is run when you use
    the Phial command line tool.

    """

    # We want all of the relative paths in the user's code to be relative to
    # the source directory, so we're actually going to modify our current
    # directory process-wide.
    old_cwd = os.getcwd()
    os.chdir(source_dir)
    log.debug("Changed into source directory %r.", source_dir)

    results = []

    # Go through every page we know about and process each one
    for i in pages._pages:
        results += process_page(i)

    # Go through every asset and process each one
    for i in pages._assets:
        results += process_asset(i)

    # During the output step, we reset the current directory back to whatever
    # it was to begin with.
    os.chdir(old_cwd)

    # Spill out the rendered pages into the output directory
    for i in results:
        destination = os.path.join(output_dir, i.target)
        if not os.path.abspath(destination).startswith(
                os.path.abspath(output_dir)):
            raise ValueError("destination path is invalid: {}".format(
                destination))

        # Make sure the destination's directory exists
        _mkdirs(os.path.dirname(destination))

        if isinstance(i, pages.RenderedPage):
            with open(destination, "w") as f:
                if isinstance(i.content, unicode):
                    f.write(i.content.encode("utf_8"))
                else:
                    f.write(i.content)
        else: # it's a ResolvedAsset
            shutil.copy(os.path.join(source_dir, i.target), destination)

def resolve_target(raw_target, source):
    """
    Resolves a target string with the provided source.

    :param raw_target: The unresolved target string (ex:
            ``projects/{name}.htm``)
    :param source: A Document instance or a file path (the same as what gets
            passed to a Page's func).

    :returns: The resulting file path.

    """

    # We're going to collect information we'll give to str.format()
    target_info = {}

    if source is not None:
        # The source is either a Document or a path
        if isinstance(source, documents.Document):
            source_path = source.file_path
            target_info["frontmatter"] = source.frontmatter
        else:
            source_path = source

        # Give format lots of info on the file's path
        target_info.update({
            "path": source_path,
            "dir": os.path.dirname(source_path),
            "fullname": os.path.basename(source_path),
            "name": os.path.splitext(os.path.basename(source_path))[0],
        })

    # Actually run format on the string and resolve it now
    return raw_target.format(**target_info)

def _resolve_result(result, page, source):
    """
    Transforms a result as returned by a page function and transforms it
    into an appropriate RenderedPage or ResolvedAsset object.

    """

    # If the user returned just content, package it up into a RenderedPage
    if not isinstance(result, (pages.RenderedPage, pages.ResolvedAsset)):
        result = pages.RenderedPage(target = None, content = result)

    # If the user didn't explictly provide a target in their return value,
    # and there the page has a target listed...
    if result.target is None and page.target is not None:
        result.target = resolve_target(page.target, source)

    # If no path is provided by the user but we have a source, we default
    # to using the source's path as the target path as well.
    if result.target is None and source is not None:
        # The source can be a document or a file path
        if isinstance(source, documents.Document):
            result.target = source.file_path
        else:
            result.target = source

    # If the result still doesn't have a target a this point we don't have
    # enough information to figure it out.
    if result.target is None:
        raise RuntimeError("not enough informaton to resolve target for "
            "{!r}".format(page))

    return result

def process_page(page):
    """
    Processes a single page and returns a list of RenderedPage and/or
    ResolvedAsset objects.

    """

    results = []
    if page.files is None:
        # The page doesn't expect any files so just call it without arguments
        result = page.func()

        result = _resolve_result(result, page, None)
        results.append(result)
    else:
        # We're going to execute the page function with each file we find
        for path in utils.glob_files(page.files):
            # Only open and parse the file if we're supposed to
            if page.parse_files:
                source = documents.Document(path)
            else:
                source = path

            # Execute the page function and get whatever the user returns
            result = page.func(source)

            if result is None:
                continue

            result = _resolve_result(result, page, source)
            results.append(result)

    return results

def process_asset(asset):
    results = []
    for path in utils.glob_files(asset.files):
        resolved = pages.ResolvedAsset(target = None, source = path)
        if asset.target is not None:
            resolved.target = _resolve_target(asset.target, path)
        else:
            resolved.target = path

        results.append(resolved)

    return results
