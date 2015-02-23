import phial


@phial.page
def homepage():
    return phial.file(name="index.htm", content="Hello World!")
