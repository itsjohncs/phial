from phial import page

@page("index.htm")
def homepage():
    return "Hello World!"
