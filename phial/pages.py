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

# These are the only symbols that will be imported when `from pages import *`
# is used.
__all__ = ["register_page", "register_assets", "register_simple_assets",
    "page", "RenderedPage", "ResolvedAsset"]

# internal
from . import exceptions
from . import documents
from . import utils

# set up logging
import logging
log = logging.getLogger(__name__)

_pages = []
"""A list of all of the pages registered in the application. """

_assets = []
"""A list of all registered assets."""

def register_page(func, *args, **kwargs):
    _pages.append(Page(func, *args, **kwargs))
    log.debug("Collected page with function %r from module %r.", func.__name__,
        func.__module__)

def register_assets(target, *files):
    _assets.append(Asset(target, files))

def register_simple_assets(*files):
    register_assets(None, *files)

def page(*dec_args, **dec_kwargs):
    # The way decorators with arguments work is that we need to return another
    # decorator that takes in a function, then that decorator will be applied
    # to the function.
    def real_decorator(function):
        # The only thing this decorator does is add the function and its
        # arguments to the list of known pages.
        register_page(function, *dec_args, **dec_kwargs)

        # We don't do the typical decorator thing of wrapping the function so
        # just return the function unchanged.
        return function

    return real_decorator

class RenderedPage(object):
    """
    Represents a single page (rather than a type of page like pages.Page
    objects). The page can be an HTML file, a CSS stylesheet, a cat picture,
    or even a blank file.

    :ivar target: The path (relative to the output directory) that the content
            should be written into.
    :ivar content: The page's content. Can either be a ``unicode`` object (in
            which case it will be written to the target file using the
            configured output encoding) or a ``str`` object (it will be
            written directly to the file).

    """

    def __init__(self, target, content):
        self.target = target
        self.content = content

class ResolvedAsset(object):
    """
    Represents a single static page. Static in this case means that no
    processing has to be done on the contents of the source file.

    :ivar target: The path (relative to the output directory) that the source
            should be copied to.
    :ivar source: The path (relative to the source directory) of the file to
            be copied.
    """

    def __init__(self, target, source):
        self.target = target
        self.source = source

    def __repr__(self):
        return "ResolvedAsset(target = {!r}, source = {!r})".format(
            self.target, self.source)

class Asset(object):
    """
    Conceptually represents a glob of static pages. Static in this case means
    that no processing has to be done on the contents of the source file(s).

    :ivar target: The path (relative to the output directory) that the source
            file will be copied to. Similarly to Path.target,  this string will
            be run through `str.format() <http://docs.python.org/2/library/stdtypes.html#str.format>`_
            for each file.
    :ivar files: May be a string, or a list of strings.  If a string, that string will be globbed, if a list of strings, each string in the list will be globbed. All matching files will be copied to the target.

    """

    def __init__(self, target, files):
        self.target = target
        self.files = files

class Page(object):
    """
    Conceptually represents a type of page on a site (ex: a project page, the
    home page, or a blog post). Pages always have a function associated with
    them that produces the actual content.

    :ivar func: The function that will be called to generate the page.
    :ivar target: The desired relative target of the page. This string will be
            run through `str.format() <http://docs.python.org/2/library/stdtypes.html#str.format>`_
            for each file. If ``None``, a ``RenderedPage`` object must be
            returned by ``func`` that specifies an explicit ``target``.
    :ivar files: May be ``None``, a string, or a list of strings.  If a
            string, that string will be globbed and ``func`` will be called
            for each unique matching file. If a list of strings, each
            string in the list will be globbed and then ``func`` will be
            called for each unique matching file. If ``None``, ``func``
            will be called only once.
    :ivar parse_files: If True each file will be opened and a Document
            object will be given to your function. Any frontmatter in the
            file will be parsed out. If False, your function will only
            receive the path of the matched file.

    """

    def __init__(self, func, target = None, files = None, parse_files = True):
        self.func = func
        self.target = target
        self.files = files
        self.parse_files = parse_files

    def __repr__(self):
        return ("Page(func = {!r}, target = {!r}, files = {!r}, "
            "parse_files = {!r}").format(self.func, self.target, self.files,
                self.parse_files)
