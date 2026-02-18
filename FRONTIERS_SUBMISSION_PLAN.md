# Frontiers Paper Submission Preparation Plan

## Context

This plan addresses preparing the DNA synthesis screening paper for Frontiers journal submission. The paper evaluates AI-assisted customer verification for synthetic biology screening, comparing 5 LLMs against human baseline across verification tasks. Key findings show the best AI model (Gemini 2.5 Pro) achieved 89.8% pass rate vs 79.5% human baseline at $1.18 vs $14.04 cost—a 10-fold reduction.

**Google Docs is ground truth** - All content has been pre-downloaded for remote session access (no authentication required). The task involves processing the downloaded Google Doc content, addressing unresolved comments, converting to Frontiers LaTeX format, and creating a submission-ready package.

## Pre-Downloaded Materials (✅ COMPLETED)

**Google Doc Content Retrieved:**
- **Source:** `1uqpLplZZVsVDZ9k5S3By2Ujg47yjf7KINtxGtpEv434`
- **Title:** Copy of 2026_01_AI-KYC_Full_text_draft
- **Status:** 11,175 words, 35 open comments, 51 resolved comments
- **Last Modified:** 2026-02-17

**Available in `final-submission/source/`:**
- `google_doc_content.md` - Clean manuscript content (authoritative source)
- `google_doc_with_comments.md` - Content with inline comment annotations
- `unresolved_comments.txt` - 35 open comments requiring attention
- `all_comments.txt` - Complete comment history for reference

**Frontiers Templates Ready:** Complete LaTeX package in `final-submission/templates/`

## Implementation Plan

### Phase 1: Content Analysis and Setup Verification (30 min)

**✅ COMPLETED: All Content Pre-Downloaded**
- Google Doc content: `final-submission/source/google_doc_content.md` (2.1MB)
- Google Doc with comments: `final-submission/source/google_doc_with_comments.md` (2.1MB)
- Unresolved comments: `final-submission/source/unresolved_comments.txt` (35 open comments)
- All comments history: `final-submission/source/all_comments.txt` (86 total comments)
- Frontiers LaTeX templates: `final-submission/templates/` (complete package)
- Project structure: `final-submission/` (fully organized)

**1.1 Content Verification**
- Verify Google Doc content integrity (11,175 words from authoritative source)
- Review critical unresolved comments requiring immediate attention
- Confirm LaTeX template compatibility and required packages
- Validate figure directory access (`paper/figures/`, `paper/new-plots/`)

**1.3 Create Complete Project Structure**
```
final-submission/
├── manuscript/
│   ├── main.tex                    # Main paper LaTeX
│   ├── references.bib              # Bibliography
│   ├── figures/                    # Main figures (1-5)
│   └── tables/                     # LaTeX table definitions
├── supplementary/
│   ├── supplementary.tex           # Appendix LaTeX
│   ├── figures/                    # Supplementary figures
│   └── README.md                   # Figure documentation
├── templates/                      # Frontiers LaTeX templates
├── source/
│   ├── google_doc_content.md       # Downloaded Google Doc
│   ├── unresolved_comments.json    # Comments to address
│   └── comment_resolutions.md      # Tracking document
└── submission_package/             # Final files for upload
```

**1.4 Initial Commit**
- Stage all downloaded content and created structure
- Commit with message: "Initial setup: Google Doc download, Frontiers templates, project structure"
- This creates the starting point for the Claude Code Web session fork

### Phase 2: Comment Analysis and Resolution Planning (45 min)

**2.1 Google Doc Analysis**
- Use Google Doc content as the authoritative source
- Parse unresolved comments and categorize by type (content, citations, figures, formatting)
- Create targeted edit suggestions for each unresolved comment
- Document specific changes needed in `comment_resolutions.md`

**2.2 Citation and Reference Resolution**
- Identify all citation placeholders and incomplete references
- Extract bibliography requirements from Google Doc content
- Address specific citation-related comments from collaborators

### Phase 3: Figure Curation and Organization (60 min)

**3.1 Main Paper Figures (5 figures)**
From existing `paper/figures/`:
1. `figure1_methodology_diagram.png` - Evaluation methodology
2. `figure2_pass_rates_heatmap.png` - Pass rates heatmap (main result)
3. `figure3_cost_breakdown.png` - Cost breakdown by model
4. `figure4_cost_vs_performance.png` - Cost vs performance scatter
5. `figure5_flag_errors_by_task_region.png` - Geographic error analysis

**3.2 Supplementary Figures Selection (15-20 figures)**
Based on appendix structure from `paper/appendix_figures.md`:
- **Appendix E** (Model Performance): 8 figures (E1-E8)
- **Appendix F** (Full Dataset): 5 figures (F1-F5)
- **Appendix G** (Flag Accuracy): 9 figures (G1-G9)
- **Appendix H** (Cost/Latency): 7 figures (H1-H7)
- **Appendix I** (Source Usage): 6 figures (I1-I6)

**3.3 Figure Organization**
- Copy selected figures to final-submission structure
- Rename according to Frontiers conventions
- Create comprehensive captions following journal guidelines
- Document all figure sources and creation methods

### Phase 4: LaTeX Conversion (90 min)

**4.1 Document Structure Setup**
- Use FrontiersinHarvard.cls document class
- Configure metadata: authors, affiliations, correspondence
- Set up required sections per Frontiers format
- Integrate Google Doc content as primary source

**4.2 Content Conversion**
- Convert Google Doc markdown to LaTeX formatting
- Transform tables to LaTeX `tabular` environments
- Handle mathematical expressions and equations
- Apply proper sectioning and formatting

**4.3 Citation and Bibliography**
- Create comprehensive BibTeX database
- Configure Frontiers Harvard citation style
- Replace all citation placeholders with proper references
- Integrate citation requirements from unresolved comments

### Phase 5: Supplementary Material Creation (45 min)

**5.1 Supplementary Document**
- Use `frontiers_SupplementaryMaterial.tex` template
- Convert appendix content maintaining current structure (5 sections)
- Integrate selected supplementary figures
- Cross-reference with main document

**5.2 Figure Integration**
- Organize supplementary figures by appendix section
- Create detailed captions for all supplementary content
- Ensure proper numbering and referencing system

### Phase 6: Compilation and Quality Assurance (45 min)

**6.1 LaTeX Compilation**
- Test main document: `pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex`
- Test supplementary material compilation
- Resolve package dependencies and logo file requirements
- Ensure clean compilation without errors

**6.2 Content Validation**
- Verify all figure references resolve correctly
- Check table formatting and alignment
- Validate citation compliance with Frontiers standards
- Ensure line numbering and spacing requirements

### Phase 7: Final Submission Package (30 min)

**7.1 Package Organization**
Required files per Frontiers submission guidelines:
- `main.tex` - Main LaTeX source
- `main.pdf` - Compiled main document
- `supplementary.tex` - Supplementary LaTeX source
- `supplementary.pdf` - Compiled supplementary material
- `references.bib` - Bibliography file
- Individual figures: `figure_01.png` through `figure_05.png`
- All supplementary figures in numerical order

**7.2 Final Validation**
- Verify file naming conventions
- Check PDF output quality and compliance
- Ensure complete submission package
- Create submission checklist

## Critical Files and Dependencies

- **Google Doc URL**: https://docs.google.com/document/d/1uqpLplZZVsVDZ9k5S3By2Ujg47yjf7KINtxGtpEv434/edit?usp=sharing (ground truth)
- **Frontiers templates**: `/Users/alejo/Downloads/Frontiers_LaTeX_Templates/` (complete package)
- **Figure assets**: `/Users/alejo/code/cliver/frontiers-results/paper/` (figures/, new-plots/, appendix_figures.md)
- **Tools required**: gdoc CLI, LaTeX installation, Google API credentials

## Success Criteria

- [ ] Complete tool installation and authentication setup
- [ ] Google Doc content downloaded with all unresolved comments extracted
- [ ] All required dependencies and templates copied to working directory
- [ ] Initial commit completed as starting point for web session fork
- [ ] Targeted resolutions created for all unresolved comments
- [ ] Complete LaTeX conversion maintaining scientific accuracy
- [ ] All figures properly integrated with appropriate captions
- [ ] Clean LaTeX compilation producing publication-ready PDFs
- [ ] Final submission package meeting Frontiers requirements

## Notes for Claude Code Web Session

After Phase 1 completion and initial commit, the project will be forked to a Claude Code Web session. The web session will have:
- Complete project structure in `final-submission/`
- All downloaded content and templates
- Clear documentation of unresolved comments requiring attention
- Established workflow for remaining phases

The web session can continue with Phase 2 (content analysis) through Phase 7 (final package) using the prepared foundation.