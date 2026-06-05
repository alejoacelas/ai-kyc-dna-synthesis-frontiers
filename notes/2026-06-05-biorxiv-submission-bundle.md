# BioRxiv Submission Bundle

## Outcome

Created `submissions/biorxiv/` as an additive BioRxiv revision bundle for the current Frontiers-submission manuscript.

Included:

- `main.tex` / `main.pdf`
- `supplementary.tex` / `supplementary.pdf`
- `references.bib`
- `figures/`
- `README.md`
- `submission-fields.md`

## Conversion Approach

I inspected the previous `biorxiv-submission` branch and reused its submission style:

- plain `article` class instead of the Frontiers classes
- `natbib` with `plainnat`
- no Frontiers macros or line numbering
- main figures/tables interleaved into the manuscript body
- separate plain-article supplementary material

The manuscript content, references, author list, and supplementary content were taken from the current branch.

## Verification

Generated the full figure set with:

```bash
make figures
```

Compiled:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex
```

Final PDFs:

- `submissions/biorxiv/main.pdf`: 27 pages
- `submissions/biorxiv/supplementary.pdf`: 43 pages

One compile fix was needed: `supplementary.tex` uses `\text{...}` in math captions, so the BioRxiv plain-article supplement now loads `amsmath`.

## BioRxiv Form Research

Checked official BioRxiv guidance for form expectations:

- Screening notes: complete metadata, special characters, research-article scope
  https://connect.biorxiv.org/news/2022/06/13/screening_procedures
- Subject areas: Synthetic Biology and Bioengineering are available
  https://connect.biorxiv.org/relate/content/181/span/2253
- Funder metadata: dedicated funder and grant-number fields
  https://connect.biorxiv.org/news/2025/09/04/funder_information
- Formatting: BioRxiv does not require a particular article format/style
  https://connect.biorxiv.org/news/2022/02/25/full_text_print

Used those checks to create `submissions/biorxiv/submission-fields.md`.
