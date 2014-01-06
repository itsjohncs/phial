Documents
=========

A Phial document can be any file. If the document contains YAML frontmatter, Phial will consume and parse it seperately from the rest of the document.

Frontmatter begins with three dashes ``---``, and ends with three periods ``...``. This is slightly different than the popular tool `Jekyll <http://jekyllrb.com/>`_ which uses three dashes to start *and* end the frontmatter, so be wary.

Below is an example of a simple document containing frontmatter.

.. code-block:: text

    # simple_document.txt
    # Comments at the top are legal! Just make sure they only exist at the top
    # and there's no spaces before the sha (# character).
    ---
    name: Phial
    author: John Sullivan
    url: https://github.com/brownhead/phial
    ...

    Phial is a simple static site generator for Python developers.

To parse a document, use Phial's Document class.

.. code-block:: python

    >>> doc = Document("simple_document.txt")
    >>> doc.frontmatter
    {
        u'name': u'Phial',
        u'author': u'John Sullivan',
        u'url': u'https://github.com/brownhead/phial'
    }
    >>> doc.body
    u'\nPhial is a simple static site generator for Python developers.''

Notice that all of the strings provided by Phial are unicode strings. Be wary of this when writing your application code.

The encoding your document uses must be either UTF-8 or UTF-16. BOM characters will be correctly handled in either case. The rules for determining the encoding follow `those laid out by the YAML 1.1 standard <http://yaml.org/spec/1.1/#id868742>`_.
