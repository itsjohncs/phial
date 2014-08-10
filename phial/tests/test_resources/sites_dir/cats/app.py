import phial

phial.assets("./", "css/*")

cats = []


@phial.pages("cats/{0}.htm", foreach="cats/*")
def bio_page(target, item):
    frontmatter, content = phial.parse_frontmatter(item)

    cats.append({"target": target, "name": frontmatter["name"]})

    template = phial.open_file("bio_template.htm").read()
    return template.format(content=content.read(), **frontmatter)


@phial.page("index.htm")
def main_page():
    links = "".join(['<li><a href="{target}">{name}</a></li>'.format(**i) for i in cats])

    template = phial.open_file("main_template.htm").read()
    return template.format(links=links)
