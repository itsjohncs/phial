#!/usr/bin/env python

# stdlib
import os
from setuptools import setup, find_packages

def read(fname):
    """
    Returns the contents of the file in the top level directory with the name
    ``fname``.

    """

    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def get_files(path):
    """
    Returns a list of the files under ``path``. The returned paths are
    relative to ``path``.

    """

    relative_to = os.path.dirname(path)
    result = []
    for dirpath, dirnames, filenames in os.walk(path):
        result += [os.path.relpath(os.path.join(dirpath, i), relative_to)
            for i in filenames]
    return result

setup(
    name = "phial",
    version = read("VERSION").strip(),
    author = "John Sullivan and other contributers",
    author_email = "john@galahgroup.com",
    description = (
        "A static website generator that takes motivation from Flask and "
        "Jekyll."
    ),
    license = "Apache v2.0",
    keywords = "python ssg",
    url = "https://www.github.com/brownhead/phial",
    long_description = "See https://www.github.com/brownhead/phial",
    install_requires = [
        "PyYAML>=3.10"
    ],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License"
    ],
    entry_points = {
        "console_scripts": [
            "phial = phial.tool:main"
        ]
    },
    # This ensures that the MANIFEST.IN file is used for both binary and source
    # distributions.
    include_package_data = True,
    packages = find_packages(),
    zip_safe = True
)
