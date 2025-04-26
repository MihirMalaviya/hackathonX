# this is for markdown to html conversion
import markdown


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
