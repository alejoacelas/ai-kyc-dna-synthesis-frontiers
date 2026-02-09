#!/usr/bin/env python3
"""Convert the React JSX diagram to a pure SVG file."""
import re
import base64
from pathlib import Path

# Read the JSX file
jsx_path = Path(__file__).parent / "diagram.jsx"
jsx_content = jsx_path.read_text()

# Extract the SVG portion (between return ( and the closing );)
svg_match = re.search(r'return \(\s*(<svg[\s\S]*?</svg>)\s*\);', jsx_content)
if not svg_match:
    raise ValueError("Could not find SVG in JSX file")

svg_content = svg_match.group(1)

# Color mappings from the JSX
colors = {
    'colors.blue': '#3B82F6',
    'colors.orange': '#F97316',
    'colors.green': '#22C55E',
    'colors.purple': '#A855F7',
    'colors.gray': '#6B7280',
    'colors.lightGray': '#E5E7EB',
    'colors.darkGray': '#374151',
    'colors.white': '#FFFFFF',
    'colors.bgLight': '#F9FAFB',
}

# Replace JSX expressions with quoted values for proper XML attributes
for jsx_expr, value in colors.items():
    svg_content = svg_content.replace(f'={{{jsx_expr}}}', f'="{value}"')

# Convert JSX comments {/* ... */} to XML comments <!-- ... -->
svg_content = re.sub(r'\{/\*\s*(.*?)\s*\*/\}', r'<!-- \1 -->', svg_content)

# Remove JSX template literal syntax from style block: {` ... `}
svg_content = re.sub(r'\{`\s*', '', svg_content)
svg_content = re.sub(r'\s*`\}', '', svg_content)

# Replace className with class
svg_content = svg_content.replace('className=', 'class=')

# Convert emoji elements to use explicit font-family for CairoSVG compatibility
# Handle tspan with fontSize: <tspan fontSize="9" class="emoji">X</tspan>
svg_content = re.sub(
    r'<tspan font-size="(\d+)" class="emoji">([^<]+)</tspan>',
    r'<tspan font-size="\1" font-family="Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji">\2</tspan>',
    svg_content
)
# Handle tspan without fontSize: <tspan class="emoji">X</tspan>
svg_content = re.sub(
    r'<tspan class="emoji">([^<]+)</tspan>',
    r'<tspan font-family="Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji">\1</tspan>',
    svg_content
)
# Handle standalone text: <text ... class="emoji">X</text>
svg_content = re.sub(
    r'<text ([^>]*)class="emoji"([^>]*)>([^<]+)</text>',
    r'<text \1font-family="Apple Color Emoji, Segoe UI Emoji, Noto Color Emoji"\2>\3</text>',
    svg_content
)

# Replace textAnchor with text-anchor
svg_content = svg_content.replace('textAnchor=', 'text-anchor=')

# Replace fillOpacity with fill-opacity
svg_content = svg_content.replace('fillOpacity=', 'fill-opacity=')

# Replace strokeWidth with stroke-width
svg_content = svg_content.replace('strokeWidth=', 'stroke-width=')

# Replace strokeDasharray with stroke-dasharray
svg_content = svg_content.replace('strokeDasharray=', 'stroke-dasharray=')

# Replace strokeOpacity with stroke-opacity
svg_content = svg_content.replace('strokeOpacity=', 'stroke-opacity=')

# Replace markerEnd with marker-end
svg_content = svg_content.replace('markerEnd=', 'marker-end=')

# Replace fontWeight with font-weight
svg_content = svg_content.replace('fontWeight=', 'font-weight=')

# Replace fontStyle with font-style
svg_content = svg_content.replace('fontStyle=', 'font-style=')

# Replace fontSize with font-size
svg_content = svg_content.replace('fontSize=', 'font-size=')

# Embed images as base64 data URIs for portability
wip_dir = Path(__file__).parent

def embed_image(filename, mime_type):
    """Convert image file to base64 data URI."""
    filepath = wip_dir / filename
    if filepath.exists():
        data = filepath.read_bytes()
        b64 = base64.b64encode(data).decode('utf-8')
        return f'data:{mime_type};base64,{b64}'
    return filename

svg_content = svg_content.replace(
    'href="web-search-logo.png"',
    f'href="{embed_image("web-search-logo.png", "image/png")}"'
)
svg_content = svg_content.replace(
    'href="ita-logo.svg"',
    f'href="{embed_image("ita-logo.svg", "image/svg+xml")}"'
)
svg_content = svg_content.replace(
    'href="europe-pmc-log.png"',
    f'href="{embed_image("europe-pmc-log.png", "image/png")}"'
)
svg_content = svg_content.replace(
    'href="orcid-logo.png"',
    f'href="{embed_image("orcid-logo.png", "image/png")}"'
)

# Add XML declaration and namespace with xlink for image support
full_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" {svg_content[4:]}'''

# Save to figures folder
output_path = Path(__file__).parent.parent / "figure0_methodology_diagram.svg"
output_path.write_text(full_svg)
print(f"SVG saved to {output_path}")

# Also convert to PNG
try:
    import cairosvg
    png_path = output_path.with_suffix('.png')
    cairosvg.svg2png(
        url=str(output_path),
        write_to=str(png_path),
        output_width=1800
    )
    print(f"PNG saved to {png_path}")
except Exception as e:
    print(f"Could not convert to PNG: {e}")
