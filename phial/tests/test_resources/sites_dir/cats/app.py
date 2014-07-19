from phial import page, open_file, register_simple_assets

register_simple_assets("styles.css", "images/*")

cats = []

@page("cats/{name}.htm", files = "cats/*.htm")
def bio_page(source, target):
    # Page functions are executed in the order in which they are declared
    # so the `cats` list will have all of the cats by the time we get to
    # the main_page() function.
    cats.append({"target": target, "name": source.frontmatter["name"]})

    template = open_file("bio_template.htm").read()
    return template.format(content = source.content, **source.frontmatter)

@page("index.htm")
def main_page():
    links = "".join(
    	['<li><a href="{target}">{name}</a></li>'.format(**i) for i in cats])

    template = open_file("main_template.htm").read()
    return template.format(links = links)
