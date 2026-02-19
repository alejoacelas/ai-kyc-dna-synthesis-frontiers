# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Convert LaTeX manuscript to clean Markdown suitable for Google Docs upload via gdoc.

Runs pandoc on the input .tex file, then post-processes the output to:
- Convert <figure> HTML blocks to markdown image syntax with absolute paths
- Replace cross-reference <a> tags with plain text (Figure N, Table N)
- Clean up <span class="math inline"> wrappers
- Remove <div> wrappers around tables
- Convert promptbox/promptlisting divs to blockquotes/code blocks
- Strip the pandoc reference list div wrappers
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_IMAGE_DIMENSION = 2400  # max pixels on longest side for Google Docs


def run_pandoc(tex_path: Path, bibliography: Path | None = None) -> str:
    """Run pandoc on a .tex file and return GFM markdown."""
    cmd = [
        "pandoc",
        str(tex_path),
        "-f", "latex",
        "-t", "gfm",
        "--wrap=none",
    ]
    if bibliography:
        cmd.extend(["--citeproc", f"--bibliography={bibliography}"])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tex_path.parent)
    if result.returncode != 0:
        print(f"pandoc stderr:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def resize_image_if_needed(src_path: Path, output_dir: Path) -> Path:
    """Copy image to output_dir, resizing if dimensions exceed MAX_IMAGE_DIMENSION."""
    dest = output_dir / src_path.name
    if dest.exists():
        return dest
    shutil.copy2(src_path, dest)
    # Check dimensions using sips (macOS)
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(dest)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        w_match = re.search(r"pixelWidth:\s*(\d+)", result.stdout)
        h_match = re.search(r"pixelHeight:\s*(\d+)", result.stdout)
        if w_match and h_match:
            w, h = int(w_match.group(1)), int(h_match.group(1))
            longest = max(w, h)
            if longest > MAX_IMAGE_DIMENSION:
                scale = MAX_IMAGE_DIMENSION / longest
                new_w, new_h = int(w * scale), int(h * scale)
                subprocess.run(
                    ["sips", "--resampleHeightWidth", str(new_h), str(new_w), str(dest)],
                    capture_output=True,
                )
                print(f"  Resized {src_path.name}: {w}×{h} → {new_w}×{new_h}")
    return dest


def convert_figures(md: str, figures_dir: Path, img_output_dir: Path | None = None) -> str:
    """Convert <figure><img><figcaption> HTML blocks to markdown image syntax."""
    def replace_figure(m: re.Match) -> str:
        src = m.group("src")
        caption = m.group("caption").strip()
        # Clean up caption: remove remaining HTML tags
        caption = re.sub(r"</?strong>", "**", caption)
        caption = re.sub(r"<[^>]+>", "", caption)
        caption = caption.replace("\n", " ").strip()
        # Resolve image path to absolute
        img_path = (figures_dir / src).resolve()
        if not img_path.exists():
            img_path = (figures_dir.parent / src).resolve()
        # Resize if needed
        if img_output_dir and img_path.exists():
            img_path = resize_image_if_needed(img_path, img_output_dir)
        return f"![{caption}]({img_path})\n"

    pattern = re.compile(
        r'<figure[^>]*>\s*'
        r'<img\s+src="(?P<src>[^"]+)"[^/]*/>\s*'
        r'<figcaption>(?P<caption>.*?)</figcaption>\s*'
        r'</figure>',
        re.DOTALL,
    )
    return pattern.sub(replace_figure, md)


def fix_cross_references(md: str) -> str:
    """Replace <a data-reference-type="ref"> tags with plain text references.

    LaTeX like ``Figure~\\ref{fig:x}`` becomes ``Figure <a ...>2</a>`` in pandoc,
    so the label word is already present. We detect this and avoid duplicating it.
    """
    def replace_ref(m: re.Match) -> str:
        prefix_word = (m.group("prefix") or "").strip()
        ref_id = m.group("ref")
        number = m.group("number").strip()

        if ref_id.startswith("fig:"):
            label = "Figure"
        elif ref_id.startswith("tab:"):
            label = "Table"
        elif ref_id.startswith("sec:"):
            label = "Section"
        else:
            return f"{prefix_word} {number}".strip() if prefix_word else number

        # If the preceding word already matches the label, don't duplicate
        if prefix_word.lower() == label.lower():
            return f"{label} {number}"
        elif prefix_word:
            return f"{prefix_word} {label} {number}"
        else:
            return f"{label} {number}"

    # Capture optional preceding word (Figure/Table/etc.) before the <a> tag
    pattern = re.compile(
        r'(?P<prefix>\w+\s+)?'
        r'<a\s+href="#[^"]*"\s+data-reference-type="ref"\s+'
        r'data-reference="(?P<ref>[^"]+)">(?P<number>[^<]+)</a>',
        re.DOTALL,
    )
    return pattern.sub(replace_ref, md)


def clean_math_inline(md: str) -> str:
    """Strip <span class="math inline"> wrappers and simplify common math."""
    # Extract content from math inline spans
    def replace_math(m: re.Match) -> str:
        content = m.group(1).strip()
        # Remove <em> tags (pandoc wraps variable names in italics)
        content = re.sub(r"</?em>", "", content)
        # Common substitutions
        content = content.replace("×", "×")
        content = content.replace("∼", "~")
        content = content.replace("−", "-")
        content = content.replace("&lt;", "<")
        content = content.replace("&gt;", ">")
        content = content.replace("&amp;", "&")
        # Clean up $ signs that pandoc sometimes leaves
        content = content.strip("$` ")
        return content

    pattern = re.compile(r'<span\s+class="math inline">(.+?)</span>', re.DOTALL)
    return pattern.sub(replace_math, md)


def clean_nocase_spans(md: str) -> str:
    """Remove <span class="nocase"> wrappers from bibliography entries."""
    return re.sub(r'<span class="nocase">([^<]+)</span>', r"\1", md)


def clean_table_divs(md: str) -> str:
    """Remove <div id="tab:..."> wrappers around tables."""
    # Remove opening div with table ID
    md = re.sub(r'<div id="tab:[^"]*">\s*\n?', "", md)
    # Remove closing </div> on standalone lines
    md = re.sub(r'^\s*</div>\s*$', "", md, flags=re.MULTILINE)
    return md


def convert_promptbox(md: str) -> str:
    """Convert <div class="promptbox"> content to blockquotes.

    Handles cases where </div> may be missing (already stripped) by matching
    until the next section heading or another <div> or end of string.
    """
    def replace_promptbox(m: re.Match) -> str:
        content = m.group(1).strip()
        lines = content.split("\n")
        quoted = "\n".join(f"> {line}" if line.strip() else ">" for line in lines)
        return quoted

    # First try matching with explicit </div>
    pattern = re.compile(r'<div class="promptbox">\s*\n?(.*?)\n?</div>', re.DOTALL)
    md = pattern.sub(replace_promptbox, md)
    # Then handle cases where </div> was already removed: match until next heading or div
    pattern2 = re.compile(
        r'<div class="promptbox">\s*\n?(.*?)(?=\n##|\n<div|\Z)', re.DOTALL
    )
    md = pattern2.sub(replace_promptbox, md)
    return md


def convert_promptlisting(md: str) -> str:
    """Convert <div class="promptlisting"> content to fenced code blocks.

    Handles cases where </div> may be missing (already stripped).
    """
    def replace_listing(m: re.Match) -> str:
        content = m.group(1).strip()
        return f"```\n{content}\n```"

    # First try with explicit </div>
    pattern = re.compile(r'<div class="promptlisting">\s*\n?(.*?)\n?</div>', re.DOTALL)
    md = pattern.sub(replace_listing, md)
    # Then handle cases where </div> was already removed
    pattern2 = re.compile(
        r'<div class="promptlisting">\s*\n?(.*?)(?=\n##|\n<div|\Z)', re.DOTALL
    )
    md = pattern2.sub(replace_listing, md)
    return md


def clean_reference_divs(md: str) -> str:
    """Clean up pandoc's reference list div wrappers."""
    # Remove the outer refs div
    md = re.sub(r'<div id="refs"[^>]*>\s*\n?', "", md)
    # Remove individual reference entry divs
    md = re.sub(r'<div id="ref-[^"]*"[^>]*>\s*\n?', "", md)
    # Remove </div> on standalone lines (leftover from above)
    # But be conservative: only remove if preceded by a blank line or start of text
    md = re.sub(r'\n</div>\s*\n', "\n\n", md)
    return md


def clean_uri_links(md: str) -> str:
    """Convert <a href="..." class="uri">Https://...</a> to plain URLs."""
    pattern = re.compile(r'<a\s+href="([^"]+)"\s+class="uri">[^<]+</a>')
    return pattern.sub(r"\1", md)


def clean_escaped_dollars(md: str) -> str:
    """Remove backslash-escaping on dollar signs that pandoc adds."""
    return md.replace(r"\$", "$")


def clean_gfm_math(md: str) -> str:
    """Convert GFM math like $`R^2 = 0.01`$ to plain text."""
    def replace_gfm_math(m: re.Match) -> str:
        content = m.group(1)
        # R^2 -> R²
        content = content.replace("R^2", "R²")
        # kappa
        content = content.replace(r"\kappa", "κ")
        # sim
        content = content.replace(r"\sim", "~")
        content = content.replace(r"\times", "×")
        return content

    return re.sub(r'\$`([^`]+)`\$', replace_gfm_math, md)


def clean_remaining_html(md: str) -> str:
    """Remove any remaining HTML tags that shouldn't be in the final output."""
    # Remove standalone </div> tags
    md = re.sub(r'^</div>\s*$', '', md, flags=re.MULTILINE)
    # Remove empty <a> anchor tags
    md = re.sub(r'<a[^>]*></a>', '', md)
    return md


def clean_extra_blank_lines(md: str) -> str:
    """Collapse runs of 3+ blank lines to 2."""
    return re.sub(r'\n{4,}', '\n\n\n', md)


def add_title_and_abstract(md: str, tex_path: Path) -> str:
    """Extract title and abstract from the LaTeX source and prepend them.

    Pandoc skips these for custom document classes, so we recover them.
    """
    tex = tex_path.read_text()

    # Extract title
    title_match = re.search(r'\\title\[[^\]]*\]\{([^}]+)\}', tex)
    if not title_match:
        title_match = re.search(r'\\title\{([^}]+)\}', tex)
    title = title_match.group(1) if title_match else None

    # Extract authors — use a brace-counting approach since content has nested {}
    authors_match = re.search(r'\\def\\Authors\{', tex)
    authors = None
    if authors_match:
        start = authors_match.end()
        depth = 1
        i = start
        while i < len(tex) and depth > 0:
            if tex[i] == '{':
                depth += 1
            elif tex[i] == '}':
                depth -= 1
            i += 1
        authors = tex[start:i - 1]
        # Clean LaTeX formatting: remove \,$^{N}$, \,$^{N,*}$ affiliations
        authors = re.sub(r'\\,\s*\$\^\{[^}]*\}\$', '', authors)
        authors = authors.replace('~', ' ')
        authors = authors.replace('\\', '')
        authors = re.sub(r'\s+', ' ', authors).strip()

    # Extract abstract
    abstract_match = re.search(r'\\begin\{abstract\}.*?\\section\{\}\s*(.+?)\\tiny', tex, re.DOTALL)
    abstract = None
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        # Clean LaTeX formatting
        abstract = abstract.replace('\\$', '$')
        abstract = abstract.replace('\\ ', ' ')
        abstract = re.sub(r'\\citep?\{[^}]+\}', '', abstract)
        abstract = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', abstract)
        abstract = abstract.replace('\\%', '%')
        abstract = abstract.replace('~', ' ')
        abstract = re.sub(r'\s+', ' ', abstract).strip()

    # Extract keywords
    keywords_match = re.search(r'\\section\{Keywords:\}\s*(.+?)\}', tex, re.DOTALL)
    keywords = keywords_match.group(1).strip() if keywords_match else None

    # Build header
    header_parts = []
    if title:
        header_parts.append(f"# {title}\n")
    if authors:
        header_parts.append(f"{authors}\n")
    if abstract:
        header_parts.append(f"## Abstract\n\n{abstract}\n")
    if keywords:
        header_parts.append(f"**Keywords:** {keywords}\n")

    if header_parts:
        header = "\n".join(header_parts) + "\n---\n\n"
        return header + md
    return md


def postprocess(md: str, tex_path: Path, img_output_dir: Path | None = None) -> str:
    """Apply all post-processing steps."""
    figures_dir = tex_path.parent / "figures"

    md = convert_figures(md, figures_dir, img_output_dir)
    md = fix_cross_references(md)
    md = clean_math_inline(md)
    md = clean_nocase_spans(md)
    md = clean_gfm_math(md)
    # Convert custom environments before stripping generic </div> tags
    md = convert_promptbox(md)
    md = convert_promptlisting(md)
    md = clean_table_divs(md)
    md = clean_reference_divs(md)
    md = clean_uri_links(md)
    md = clean_escaped_dollars(md)
    md = clean_remaining_html(md)
    md = clean_extra_blank_lines(md)

    # Add title/abstract for manuscript (has \begin{abstract})
    if r"\begin{abstract}" in tex_path.read_text():
        md = add_title_and_abstract(md, tex_path)

    return md


def main():
    parser = argparse.ArgumentParser(description="Convert LaTeX to Google Docs-ready Markdown")
    parser.add_argument("tex_file", type=Path, help="Input .tex file")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output .md file")
    parser.add_argument("--bibliography", "-b", type=Path, help="Bibliography .bib file")
    args = parser.parse_args()

    tex_path = args.tex_file.resolve()
    if not tex_path.exists():
        print(f"Error: {tex_path} not found", file=sys.stderr)
        sys.exit(1)

    bib_path = args.bibliography.resolve() if args.bibliography else None
    if bib_path and not bib_path.exists():
        print(f"Error: {bib_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Running pandoc on {tex_path}...")
    raw_md = run_pandoc(tex_path, bib_path)

    # Create a directory next to output for resized images
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img_dir = output_path.parent / f".{output_path.stem}_images"
    img_dir.mkdir(exist_ok=True)

    print("Post-processing...")
    clean_md = postprocess(raw_md, tex_path, img_dir)

    output_path.write_text(clean_md)
    print(f"Written to {output_path}")
    print(f"Images in {img_dir}")

    # Report residual HTML (excluding expected patterns)
    all_html = re.findall(r'<(?!http)[a-z][^>]*>', clean_md)
    # Exclude: HTML table tags (complex tables stay as HTML), escaped XML in prompt content
    expected = re.compile(
        r'^<(table|thead|tbody|tr|td|th|caption|strong|em)\b'  # HTML table elements
        r'|\\>'  # escaped XML-like tags from prompt content
    )
    residual = [t for t in all_html if not expected.search(t)]
    if residual:
        unique = set(residual)
        print(f"\nWarning: {len(residual)} residual HTML tags found ({len(unique)} unique):")
        for tag in sorted(unique)[:20]:
            count = residual.count(tag)
            print(f"  {tag} ({count}x)")
    else:
        print("\nNo unexpected residual HTML tags found.")


if __name__ == "__main__":
    main()
