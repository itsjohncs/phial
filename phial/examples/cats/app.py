import phial

cats = []


@phial.pipeline("css/*")
def css(source):
    return source


@phial.pipeline("js/*")
def js(source):
    return source | phial.concat("concat.js")


@phial.page("cats/*")
def bio_page(source_file):
    template = open("bio_template.htm").read()
    frontmatter, content = phial.parse_frontmatter(source_file)

    # HACK(brownhead): #22 aims to find a better solution to this.
    cats.append({"target": source_file.name, "name": frontmatter["name"]})

    output = template.format(content=content.read(), **frontmatter)
    return phial.file(name=source_file.name, content=output)


@phial.page
def main_page():
    sorted_cats = sorted(cats, key=lambda cat: cat["name"])
    links = "".join(['<li><a href="{target}">{name}</a></li>'.format(**i) for i in sorted_cats])

    template = open("main_template.htm").read()
    return phial.file(name="index.htm", content=template.format(links=links))
