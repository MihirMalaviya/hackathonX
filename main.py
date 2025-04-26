import markdown

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

text = """

# this is some simle markdon text

```
lets test this mannnn
yay
ayasudiuahwid
asdads
```

## adshihawu

dsaadsads
""".strip()


def md2html(text: str) -> str:
    """
    converts text to html
    :param text: text to convert
    :return: html c0de
    """

    html_code = markdown.markdown(
        text,
        extensions=[
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.tables",
            "markdown.extensions.footnotes",
        ],
    )

    return html_code


with open("content.html", "w") as f:
    tempHTML = md2html(text)

    print(tempHTML)
    f.write(tempHTML)


print()
