Phial
=====

**The code in this README does not necessarily work yet, this is how I want Phial to work, not how it already works.**

Phial is a static site generator for Python developers.

.. code-block:: python

    from phial import page

    @page("index.htm")
    def homepage():
        return "Hello World!"

.. code-block:: bash

    $ pip install phial
    $ phial --testing hello.py # Serves at http://localhost:9000

What's Inluded?
---------------

Phial is unopiniated. Its small feature set includes:

* YAML frontmatter parsing
* UTF-8 and UTF-16 file support (unicode supported throughout)
* Built-in development server
* Sensible API

It does not (and never will) include:

* Any template engine
* An opinion on how you structure your site
* "Magical" features
* A huge list of dependencies

Quick Walkthrough
-----------------

As you saw above, it's certainly possible to make a Phial site that doesn't use any source files (ie: templates, documents, images, etc). Most of the time this isn't what you want though.

Here is a slightly more developed example. For the full site including the source files see `here <http://google.com>`_.

.. code-block:: python

    from phial import page, open_file, register_simple_assets

    register_simple_assets("styles.css", "images/*")

    cats = []

    @page("cats/{name}.htm", files = "cats/*.htm")
    def bio_page(source, target):
        # Page functions are executed in the order in which they are declared
        # so the `cats` list will have all of the cats by the time we get to
        # the main_page() function.
        cats.append((source.frontmatter["name"], target))

        template = open_file("bio_template.htm").read()
        return template.format(content = source.content, **source.frontmatter)

    @page("index.htm")
    def main_page():
        links = "".join(['<li><a href="{}">{}</a></li>'.format(*i) for i in cats])

        template = open_file("main_template.htm").read()
        return template.format(links = links)

I avoided using any external templating or rendering engines in this example, but there's nothing stopping you from using Mustache, Jinja2, Markdown, reStructuredText, or any other library in your app.

Sites Using Phial
-----------------

* `johncs.com <http://johncs.com>`_ (`source <https://github.com/brownhead/johncs.com>`_)
