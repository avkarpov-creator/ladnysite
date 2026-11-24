"""Check that the sitemap and DevOps links resolve in the static publish tree."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

SITE = Path(__file__).resolve().parents[1] / "site"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.references = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id":
                self.ids.add(value)
            if key in {"href", "src", "srcset"} and value:
                self.references.append(value)


def resolve(base, path):
    target = base / unquote(path)
    return target / "index.html" if target.is_dir() else target


def main():
    for entry in ElementTree.parse(SITE / "sitemap.xml").iterfind(".//{*}loc"):
        path = urlsplit(entry.text).path
        if not resolve(SITE, path.lstrip("/")).is_file():
            raise SystemExit(f"Broken sitemap entry: {entry.text}")

    home = Page(SITE / "index.html")
    if "/devops/" not in home.references:
        raise SystemExit("Missing portfolio link on the home page.")

    portfolio = SITE / "devops/index.html"
    for reference in Page(portfolio).references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            continue
        base = SITE if url.path.startswith("/") else portfolio.parent
        target = resolve(base, url.path.lstrip("/")) if url.path else portfolio
        if not target.is_file():
            raise SystemExit(f"Broken portfolio reference: {reference}")
        if url.fragment:
            if target.suffix == ".svg":
                ids = {node.get("id") for node in ElementTree.parse(target).iter()}
            else:
                ids = Page(target).ids
            if url.fragment not in ids:
                raise SystemExit(f"Broken portfolio fragment: {reference}")

    for diagram in portfolio.parent.glob("*.svg"):
        ElementTree.parse(diagram)
    print("Static site checks passed.")


if __name__ == "__main__":
    main()
