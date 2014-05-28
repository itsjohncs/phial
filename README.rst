Phial
=====

Phial is a simple Python library for building static sites.

.. code-block:: python

    # hello.py

    from phial import page

    @page("index.htm")
    def homepage():
        return "Hello World!"

.. code-block:: bash

    $ pip install phial
    $ phial --testing hello.py # Serves at http://localhost:9000

Phial is Unopiniated
--------------------

Its small feature set includes:

* YAML frontmatter parsing
* UTF-8 and UTF-16 file support (unicode supported throughout)
* Built-in development server
* Automatic reloading
* Sensible API
* Lots of love

Its small feature set does not, and never will include:

* Any template engine
* An opinion on how you structure your site
* Magical, hard to understand features
* A huge list of dependencies

Phial is made for Python Developers
-----------------------------------

I'm tired of SSG's that use extremely heavy, and extremely leaky, abstractions.

When I make a static site I want to have absolute control over everything without having to dive into the internals of some crazy plugin system. At the same time, I don't want to have to reinvent a ton of simple, convenient things like automatic reloading or running a dev server.

Phial is my solution to this frustration. Let me know what you think.

Quick Walkthrough
-----------------

As you saw in the short snippet above, it's certainly possible to make a Phial site that doesn't use any source files (ie: templates, documents, images, etc). Most of the time this isn't what you want though.

Here is a slightly more developed example.

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

If you want to see even more developed examples, check out these sites! There's only one right now but it would be awfully nice if there were more... (nudge nudge)

* `johncs.com <http://johncs.com>`_ (`source <https://github.com/brownhead/johncs.com>`_)
