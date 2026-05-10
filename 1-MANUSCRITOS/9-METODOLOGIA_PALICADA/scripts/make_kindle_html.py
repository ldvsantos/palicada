from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path


MAIN_RE = re.compile(
    r'<main[^>]*id="quarto-document-content"[^>]*>(.*?)</main>',
    re.IGNORECASE | re.DOTALL,
)
FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

SUPERSCRIPT_MAP = str.maketrans(
    {
        "0": "\u2070",
        "1": "\xb9",
        "2": "\xb2",
        "3": "\xb3",
        "4": "\u2074",
        "5": "\u2075",
        "6": "\u2076",
        "7": "\u2077",
        "8": "\u2078",
        "9": "\u2079",
        "+": "\u207a",
        "-": "\u207b",
        "=": "\u207c",
        "(": "\u207d",
        ")": "\u207e",
        "n": "\u207f",
        "i": "\u2071",
    }
)

SUBSCRIPT_MAP = str.maketrans(
    {
        "0": "\u2080",
        "1": "\u2081",
        "2": "\u2082",
        "3": "\u2083",
        "4": "\u2084",
        "5": "\u2085",
        "6": "\u2086",
        "7": "\u2087",
        "8": "\u2088",
        "9": "\u2089",
        "+": "\u208a",
        "-": "\u208b",
        "=": "\u208c",
        "(": "\u208d",
        ")": "\u208e",
        "a": "\u2090",
        "e": "\u2091",
        "h": "\u2095",
        "i": "\u1d62",
        "j": "\u2c7c",
        "k": "\u2096",
        "l": "\u2097",
        "m": "\u2098",
        "n": "\u2099",
        "o": "\u2092",
        "p": "\u209a",
        "r": "\u1d63",
        "s": "\u209b",
        "t": "\u209c",
        "u": "\u1d64",
        "v": "\u1d65",
        "x": "\u2093",
    }
)

LATEX_REPLACEMENTS = {
    r"\\cdot": "\u00b7",
    r"\\times": "\u00d7",
    r"\\leq": "\u2264",
    r"\\geq": "\u2265",
    r"\\approx": "\u2248",
    r"\\neq": "\u2260",
    r"\\phi": "\u03c6",
    r"\\gamma": "\u03b3",
    r"\\tau": "\u03c4",
    r"\\Delta": "\u0394",
    r"\\mu": "\u03bc",
    r"\\rho": "\u03c1",
    r"\\theta": "\u03b8",
    r"\\alpha": "\u03b1",
    r"\\beta": "\u03b2",
}

KINDLE_CSS = """
body {
  margin: 0;
  padding: 1.2rem;
  color: #111;
  background: #fff;
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.55;
}
main {
  max-width: 860px;
  margin: 0 auto;
}
h1, h2, h3, h4 {
  line-height: 1.25;
  margin: 1.4rem 0 0.7rem;
}
h1 {
  font-size: 1.6rem;
}
h2 {
  font-size: 1.3rem;
}
h3 {
  font-size: 1.12rem;
}
p, li, td, th {
  font-size: 1rem;
}
header.document-meta {
  border-bottom: 1px solid #bbb;
  margin-bottom: 1.25rem;
  padding-bottom: 0.8rem;
}
header.document-meta p {
  margin: 0.2rem 0;
}
img, svg {
  max-width: 100%;
  height: auto;
}
figure {
  margin: 1rem 0;
}
figcaption {
  font-size: 0.95rem;
  color: #444;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  display: block;
  overflow-x: auto;
}
th, td {
  border: 1px solid #bbb;
  padding: 0.45rem 0.5rem;
  vertical-align: top;
}
blockquote {
  margin: 1rem 0;
  padding-left: 0.9rem;
  border-left: 3px solid #bbb;
}
.equation {
  margin: 1rem 0;
  padding: 0.7rem 0.8rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  font-family: "Courier New", Courier, monospace;
  white-space: pre-wrap;
}
.math {
  font-family: "Courier New", Courier, monospace;
}
a {
  color: #000;
  text-decoration: none;
}
hr {
  border: 0;
  border-top: 1px solid #bbb;
  margin: 1.2rem 0;
}
""".strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um HTML simplificado para Kindle a partir de um QMD do Quarto."
    )
    parser.add_argument("qmd", type=Path, help="Caminho para o arquivo .qmd")
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="Nao renderiza o QMD antes de simplificar o HTML existente.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Caminho opcional do HTML final para Kindle.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_front_matter(qmd_text: str) -> tuple[str, list[str], str]:
    front_match = FRONT_MATTER_RE.match(qmd_text)
    front_matter = front_match.group(1) if front_match else ""

    title_match = re.search(r'^title:\s*"?(.*?)"?\s*$', front_matter, re.MULTILINE)
    date_match = re.search(r'^date:\s*"?(.*?)"?\s*$', front_matter, re.MULTILINE)
    author_match = re.search(
        r'^author:\s*\n((?:[ \t]+-\s*.*\n?)+)', front_matter, re.MULTILINE
    )

    title = title_match.group(1).strip() if title_match else "Documento"
    date = date_match.group(1).strip() if date_match else ""
    authors: list[str] = []

    if author_match:
        for line in author_match.group(1).splitlines():
            cleaned = re.sub(r'^[ \t]*-\s*', '', line).strip().strip('"')
            if cleaned:
                authors.append(cleaned)

    return html.unescape(title), authors, html.unescape(date)


def render_qmd(qmd_path: Path) -> None:
    command = ["quarto", "render", str(qmd_path.name)]
    subprocess.run(command, cwd=qmd_path.parent, check=True)



def extract_main(html_text: str) -> str:
    match = MAIN_RE.search(html_text)
    if not match:
        raise ValueError("Nao foi possivel localizar o conteudo principal do HTML do Quarto.")
    return match.group(1)



def convert_superscript(text: str) -> str:
    return text.translate(SUPERSCRIPT_MAP)



def convert_subscript(text: str) -> str:
    converted = text.translate(SUBSCRIPT_MAP)
    return converted if converted != text else text



def tex_to_plain(tex: str) -> str:
    plain = html.unescape(tex)
    plain = re.sub(r'^\\\(|\\\)$', '', plain)
    plain = re.sub(r'^\\\[|\\\]$', '', plain)
    plain = plain.strip()

    for pattern, replacement in LATEX_REPLACEMENTS.items():
        plain = re.sub(pattern, replacement, plain)

    plain = re.sub(r'\\text\{([^{}]+)\}', r'\1', plain)
    plain = re.sub(r'\\mathrm\{([^{}]+)\}', r'\1', plain)
    plain = re.sub(r'\\operatorname\{([^{}]+)\}', r'\1', plain)
    plain = re.sub(r'\\left|\\right', '', plain)
    plain = re.sub(r'\\tan\b', 'tan', plain)

    def fraction_repl(match: re.Match[str]) -> str:
        numerator = tex_to_plain(match.group(1))
        denominator = tex_to_plain(match.group(2))
        return f"({numerator})/({denominator})"

    def sqrt_repl(match: re.Match[str]) -> str:
        return f"\u221a({tex_to_plain(match.group(1))})"

    plain = re.sub(r'\\d?frac\{([^{}]+)\}\{([^{}]+)\}', fraction_repl, plain)
    plain = re.sub(r'\\sqrt\{([^{}]+)\}', sqrt_repl, plain)
    plain = re.sub(
        r'_\{([^{}]+)\}',
        lambda match: convert_subscript(tex_to_plain(match.group(1))),
        plain,
    )
    plain = re.sub(
        r'_([A-Za-z0-9]+)',
        lambda match: convert_subscript(match.group(1)),
        plain,
    )
    plain = re.sub(
        r'\^\{([^{}]+)\}',
        lambda match: convert_superscript(tex_to_plain(match.group(1))),
        plain,
    )
    plain = re.sub(
        r'\^([A-Za-z0-9+\-=()\-])',
        lambda match: convert_superscript(match.group(1)),
        plain,
    )
    plain = plain.replace('{', '').replace('}', '')
    plain = plain.replace('\\', '')
    plain = re.sub(r'\s+', ' ', plain)
    return plain.strip()



def replace_math(html_fragment: str) -> str:
    def inline_repl(match: re.Match[str]) -> str:
        return f'<span class="math">{html.escape(tex_to_plain(match.group(1)))}</span>'

    def display_repl(match: re.Match[str]) -> str:
        return f'<div class="equation">{html.escape(tex_to_plain(match.group(1)))}</div>'

    html_fragment = re.sub(
        r'<span[^>]*class="math inline"[^>]*>(.*?)</span>',
        inline_repl,
        html_fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html_fragment = re.sub(
        r'<span[^>]*class="math display"[^>]*>(.*?)</span>',
        display_repl,
        html_fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def mathml_repl(match: re.Match[str]) -> str:
      annotation = re.search(
        r'<annotation[^>]*application/x-tex[^>]*>(.*?)</annotation>',
        match.group(0),
        flags=re.IGNORECASE | re.DOTALL,
      )
      if annotation:
        plain = tex_to_plain(annotation.group(1))
      else:
        plain = re.sub(r'<[^>]+>', '', match.group(0))
        plain = html.unescape(plain).strip()
      return f'<span class="math">{html.escape(plain)}</span>'

    html_fragment = re.sub(
      r'<math\b.*?</math>',
      mathml_repl,
      html_fragment,
      flags=re.IGNORECASE | re.DOTALL,
    )

    return html_fragment



def cleanup_main(html_fragment: str) -> str:
    cleaned = html_fragment
    cleaned = re.sub(
        r'<header[^>]*id="title-block-header"[^>]*>.*?</header>',
        '',
        cleaned,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(r'<a[^>]*class="anchorjs-link"[^>]*>.*?</a>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<span[^>]*class="header-section-number"[^>]*>.*?</span>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'\sdata-[A-Za-z0-9_-]+="[^"]*"', '', cleaned)
    cleaned = re.sub(r'\srole="[^"]*"', '', cleaned)
    cleaned = re.sub(r'\sclass="anchored"', '', cleaned)
    cleaned = cleaned.replace('<section id="referências"></section>', '')
    cleaned = replace_math(cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()



def build_document(title: str, authors: list[str], date: str, main_html: str) -> str:
    author_line = ''
    if authors:
        author_line = f'<p><strong>Autores:</strong> {html.escape(", ".join(authors))}</p>'

    date_line = ''
    if date:
        date_line = f'<p><strong>Data:</strong> {html.escape(date)}</p>'

    return f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)} - Kindle</title>
  <style>
{KINDLE_CSS}
  </style>
</head>
<body>
  <main>
    <header class=\"document-meta\">
      <h1>{html.escape(title)}</h1>
      {author_line}
      {date_line}
    </header>
    {main_html}
  </main>
</body>
</html>
"""



def main() -> int:
    args = parse_args()
    qmd_path = args.qmd.resolve()

    if not qmd_path.exists():
        print(f"Arquivo nao encontrado: {qmd_path}", file=sys.stderr)
        return 1

    if qmd_path.suffix.lower() != ".qmd":
        print("Informe um arquivo .qmd.", file=sys.stderr)
        return 1

    if not args.skip_render:
        render_qmd(qmd_path)

    html_path = qmd_path.with_suffix(".html")
    if not html_path.exists():
        print(f"HTML renderizado nao encontrado: {html_path}", file=sys.stderr)
        return 1

    output_path = args.output.resolve() if args.output else qmd_path.with_name(f"{qmd_path.stem}_kindle.html")

    qmd_text = read_text(qmd_path)
    html_text = read_text(html_path)
    title, authors, date = parse_front_matter(qmd_text)
    main_html = cleanup_main(extract_main(html_text))
    output_path.write_text(build_document(title, authors, date, main_html), encoding="utf-8")

    print(f"HTML Kindle gerado em: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
