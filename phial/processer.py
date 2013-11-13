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
