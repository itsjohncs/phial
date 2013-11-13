from phial import *

@page("projects/<name>", files = "projects/*.md")
def projects(project):
    return render_template(project)

@page("projects"):
def project_listing():
    return render_template(File("projects.htm"))
