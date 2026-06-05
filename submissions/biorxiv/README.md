# BioRxiv submission bundle

This folder contains a BioRxiv-formatted version of the current Frontiers manuscript. It follows the earlier `biorxiv-submission` branch by using a plain `article` class, interleaving figures and tables in the main text, removing Frontiers template files/macros, and compiling with `plainnat`.

Files:

- `main.tex` / `main.pdf`: main manuscript
- `supplementary.tex` / `supplementary.pdf`: supplementary material
- `references.bib`: bibliography copied from `paper/references.bib`
- `figures/`: static and generated figures required by the manuscript and supplement
- `submission-fields.md`: copy-paste metadata for the BioRxiv revision form

To rebuild after upstream paper edits:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary.tex
```
