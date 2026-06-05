# BioRxiv Submission Fields

Prepared for the BioRxiv revision form from the current BioRxiv-formatted manuscript in this folder.

## Files To Upload

Main manuscript PDF:

```text
submissions/biorxiv/main.pdf
```

Supplementary material PDF:

```text
submissions/biorxiv/supplementary.pdf
```

If the form asks for source files, use:

```text
submissions/biorxiv/main.tex
submissions/biorxiv/supplementary.tex
submissions/biorxiv/references.bib
submissions/biorxiv/figures/
```

## Manuscript Basics

### Title

```text
Evaluating AI-Assisted Customer Verification for Synthetic Nucleic Acid Screening
```

### Article Type

```text
Research article
```

### Subject Area

Recommended:

```text
Synthetic Biology
```

Fallback if matching the previous version matters more than topical fit:

```text
Bioengineering
```

### Has this manuscript been published by a journal?

```text
No
```

### Has this manuscript been submitted to a journal?

```text
Yes
```

### Journal

```text
Frontiers
```

## Abstract

```text
Legitimacy screening, the process of verifying the identity and purpose of customers ordering synthetic nucleic acids, is a primary safeguard against the misuse of synthetic biology. However, the associated costs discourage the adoption of screening practices. To evaluate whether AI tools can facilitate this process, we tested five large language models on five verification tasks using customer profiles of life sciences researchers from around the world. We compared AI performance against an expert human baseline on flag accuracy, source quality, source fidelity, and cost.

Flag accuracy of the best-performing model (Gemini 2.5 Pro with four bibliographic and sanctions APIs) was statistically indistinguishable from the human baseline at 90.2% and 89.0% (n = 41). Gemini 2.5 Pro performed at or above the human baseline on source quality and fidelity, at roughly one-tenth of the cost ($1.18 vs. $14.04 per customer). For information-gathering tasks, which excluded the human review step, costs averaged $0.23 per customer, around 50 times cheaper than human screening. These results support piloting AI assistance at the information-gathering step of legitimacy screening at providers of synthetic nucleic acids and other dual-use biotechnology products, with human reviewers retaining authority over follow-up communication and order fulfillment decisions.
```

## Keywords

```text
biosecurity, large language models, legitimacy screening, know your customer, sequence of concern, gene synthesis, human-in-the-loop, dual-use biotechnology
```

## Author Approvals

Checkbox text from the form:

```text
All the individuals named as authors of this manuscript have approved its submission to bioRxiv.
```

Use:

```text
Yes
```

## Author List

### Alejandro Acelas

```text
First/Given name: Alejandro
Last/Family name: Acelas
Email: alejoacelas@gmail.com
Corresponding author: Yes
Affiliation 1: The Centre for Long-Term Resilience, London, United Kingdom
```

### Hanna Pálya

```text
First/Given name: Hanna
Last/Family name: Pálya
Corresponding author: No
Affiliation 1: The Centre for Long-Term Resilience, London, United Kingdom
Affiliation 2: University of Warwick, Coventry, United Kingdom
```

### Kevin Flyangolts

```text
First/Given name: Kevin
Last/Family name: Flyangolts
Corresponding author: No
Affiliation 1: Aclid, New York, United States
```

### Paul-Enguerrand Fady

```text
First/Given name: Paul-Enguerrand
Last/Family name: Fady
Corresponding author: No
Affiliation 1: The Centre for Long-Term Resilience, London, United Kingdom
```

### Cassidy Nelson

```text
First/Given name: Cassidy
Last/Family name: Nelson
Corresponding author: No
Affiliation 1: The Centre for Long-Term Resilience, London, United Kingdom
```

## Affiliations

```text
The Centre for Long-Term Resilience, London, United Kingdom
```

```text
University of Warwick, Coventry, United Kingdom
```

```text
Aclid, New York, United States
```

## Funding Information

### Funder

```text
The Centre for Long-Term Resilience
```

### Grant Number

```text
Not applicable
```

### Funding Statement

```text
This work was supported by The Centre for Long-Term Resilience.
```

## Distribution / Reuse Options

Use the same license as the existing BioRxiv version if the form shows it.

If you need to choose a license from scratch, a conservative default is:

```text
CC BY-NC-ND
```

If you want maximum reuse and funder/open-access compatibility, choose:

```text
CC BY
```

## Revision Summary

```text
This revised version updates the preprint to match the current journal-submission manuscript. Major changes include: clearer framing of the study as an evaluation of AI assistance for the information-gathering step of follow-up legitimacy screening; updated results text reporting the best model's flag accuracy as statistically indistinguishable from the human baseline; added Wilson confidence intervals, McNemar exact tests, minimum detectable effect / power analysis, and a supplementary forest plot; expanded discussion of human-in-the-loop deployment, prompt-injection risk, adversarial deception, public-information bias, and regulatory implications; clarified limitations around dataset size, ground-truth grading, human-baseline comparison, and real-world deployment; updated references, figures, tables, and supplementary material.
```

Shorter version if the field is small:

```text
Updated to match the current journal-submission manuscript. Added statistical uncertainty analyses, clarified the information-gathering scope of the evaluation, expanded limitations and deployment-risk discussion, updated references, and regenerated figures/tables and supplementary material.
```

## File Metadata

### Main Manuscript

```text
File: main.pdf
Description: Main manuscript with title page, abstract, author list, main text, references, and in-line figures/tables.
```

### Supplementary Material

```text
File: supplementary.pdf
Description: Supplementary material including sequences of concern, statistical power and confidence interval analyses, task prompts, evaluation prompts, adversarial case study, additional validation details, and supplementary figures/tables.
```

## Conflict Of Interest

```text
AA, HP, and KF are affiliated with organizations or projects that build and deploy biosecurity screening software (Cliver, Aclid). The remaining authors declare that the research was conducted in the absence of any commercial or financial relationships that could be construed as a potential conflict of interest.
```

## Data Availability

```text
The materials to replicate the main results of this work are available on GitHub at https://github.com/alejoacelas/ai-kyc-dna-synthesis-frontiers. Artefacts derived from real customer information (full screener responses and ungraded outputs) are excluded from the public release to protect personal data; this, together with reliance on proprietary LLMs whose versions evolve and exhibit stochastic outputs, limits exact replication. The published pipeline, prompts, and scoring criteria are detailed enough for other teams to construct comparable datasets and evaluations.
```

## Author Contributions

```text
AA, HP, KF, PEF, and CN contributed to the conceptualization of the study. AA, HP, and KF developed the methodology. AA developed the software, conducted the formal analysis, performed the investigation, provided resources, curated the data, and created the visualizations. HP and AA wrote the original draft. HP, KF, PEF, and CN reviewed and edited the manuscript. PEF and CN provided supervision and acquired funding. CN administered the project. All authors reviewed and approved the final manuscript.
```

## Acknowledgments

```text
We thank Becky Mackelprang at the Engineering Biology Research Consortium (EBRC) for providing the adversarial case study profile used in our evaluation, and Janika Schmitt and Tessa Alexanian for helpful comments on earlier drafts of this manuscript. We also thank Frankie Di-Nozzi for project management and operations support. Acknowledgment does not imply endorsement of the paper or its findings.

AI assistants (Claude, Anthropic; Gemini, Google) were used to proofread and suggest improvements to the manuscript text, write code for the evaluation pipeline, data analysis, figure generation, and the human evaluation interface, and to format the LaTeX submission.
```

## Biosecurity / Dual-Use Screening Note

Use only if BioRxiv asks for clarification:

```text
The manuscript evaluates screening safeguards for synthetic nucleic acid ordering. It does not provide actionable wet-lab protocols, pathogen engineering methods, or full biological sequence designs. Customer information in the public replication package is anonymized.
```

## Sources Checked For Form Expectations

- BioRxiv screening notes say in-house screeners check that submission fields are complete, special characters are coded correctly, and the article is an appropriate research manuscript: https://connect.biorxiv.org/news/2022/06/13/screening_procedures
- BioRxiv subject area list includes Synthetic Biology and Bioengineering: https://connect.biorxiv.org/relate/content/181/span/2253
- BioRxiv funder-metadata note says the submission system has dedicated funder and grant-number fields: https://connect.biorxiv.org/news/2025/09/04/funder_information
- BioRxiv notes that author PDFs vary and BioRxiv does not require a specific article format/style: https://connect.biorxiv.org/news/2022/02/25/full_text_print
