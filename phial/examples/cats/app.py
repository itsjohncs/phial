import phial


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

    output = template.format(content=content.read(), **frontmatter)
    return phial.file(
        name=source_file.name,
        metadata={"target": source_file.name, "name": frontmatter["name"]},
        content=output)


@phial.page(depends_on=bio_page)
def main_page():
    bio_task = phial.get_task(bio_page)
    cat_links = [i.metadata for i in bio_task.files]

    sorted_cats = sorted(cat_links, key=lambda link: link["name"])
    links = "".join(['<li><a href="{target}">{name}</a></li>'.format(**i) for i in sorted_cats])

    template = open("main_template.htm").read()
    return phial.file(name="index.htm", content=template.format(links=links))
