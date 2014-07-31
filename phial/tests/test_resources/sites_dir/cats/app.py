from glob import glob

from phial import *

simple_assets("styles.css", "images/*")

cats = []

@multipage("{}", foreach=glob("cats/*.htm"))
def bio_page(path, item):
    frontmatter, content = parse_frontmatter(item)

    cats.append({"target": path, "name": frontmatter["name"]})

    template = open_file("bio_template.htm").read()
    return template.format(content = content.read(), **frontmatter)

@page("index.htm")
def main_page():
    links = "".join(
    	['<li><a href="{target}">{name}</a></li>'.format(**i) for i in cats])

    template = open_file("main_template.htm").read()
    return template.format(links = links)
