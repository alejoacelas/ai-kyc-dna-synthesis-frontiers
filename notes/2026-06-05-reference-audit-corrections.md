# Reference Audit Corrections

Date: 2026-06-05

## Scope

Audited all 25 entries in `paper/references.bib` using four parallel background checks. Applied corrections to:

- `paper/references.bib`
- `submissions/biorxiv/references.bib`

The BioRxiv bibliography was kept in sync with the original paper bibliography so the new BioRxiv bundle does not preserve stale reference metadata.

## Source of the Tanya/Tessa Alexanian Mistake

The mistake was present in the original paper folder, not introduced by the BioRxiv conversion.

`git blame HEAD -L 31,59 -- paper/references.bib` showed that both incorrect `Tanya` entries were introduced in commit `7cfae02` (`Replication package for AI-assisted customer screening`, 2026-02-27):

- `Alexanian2024` had `Alexanian, Tanya and Carter, Sarah R.`
- `Wheeler2024` had `Alexanian, Tanya`

The BioRxiv copy then inherited the error because `submissions/biorxiv/references.bib` was copied from `paper/references.bib`.

Official sources identify the author as Tessa Alexanian:

- IBBIS report PDF: https://ibbis.bio/wp-content/uploads/2024/02/IBBIS_Whitepaper_2024_Verifying_Customer_Legitimacy-1.pdf
- Applied Biosafety article: https://journals.sagepub.com/doi/10.1089/apb.2023.0034

## Corrections Applied

| BibTeX key | Correction |
| --- | --- |
| `Crawford2024` | Added RAND report number `RR-A3329-1`, page count `76`, and DOI `10.7249/RRA3329-1`. |
| `CarterFriedman2015` | Added J. Craig Venter Institute URL. |
| `Alexanian2024` | Corrected `Tanya` to `Tessa`; normalized report title; added February 2024 month and IBBIS PDF URL. |
| `Cliver2025` | Updated title to match the repository README (`Cliver API User Guide`), changed year to 2026, and added access-date note. |
| `Wheeler2024` | Corrected authors to Nicole E. Wheeler, Sarah R. Carter, Tessa Alexanian, Christopher Isaac, Jaime Yassif, and Piers Millet; expanded journal to `Applied Biosafety`; added volume 29, issue 2, and pages 71--78; removed stale advance-online-publication note. |
| `EUAIAct2024` | Expanded official EU AI Act title with amendment clauses and EEA relevance text; updated Official Journal metadata to `OJ L, 2024/1689, 12 July 2024`. |
| `EUBiotechAct2025` | Expanded proposal title with amendment clauses, added procedure number `2025/0406(COD)`, and switched to the European Commission publication page. |
| `Fady2025annexes` | Added DOI `10.71172/q750-y70v` and normalized typographic quotes in the title so BibTeX/plainnat renders it correctly. |
| `HHS2023` | Expanded institution to include the Administration for Strategic Preparedness and Response and added October 2023 month. |
| `IGSC2024` | Updated title to `Harmonized Screening Protocol v3.0`, added September 2024 month, and added exact version date note. |
| `Fady2025costmodel` | Changed title to `Cost-Benefit Analysis of Synthetic Nucleic Acid Screening for the UK` and updated the spreadsheet URL to the canonical model tab. |
| `Haddad2025` | Corrected journal volume from 41 to 33. |
| `Tan2021` | Corrected author names from `Tan, Xin` and `Letendre, Jason H.` to `Tan, Xiao` and `Letendre, Justin H.`. |
| `Aclid2025` | Updated year to 2026 and added access-date note because the current site does not support a 2025 publication date. |
| `TwentyTwo2026` | Added access-date note. |
| `Zheng2023` | Updated NeurIPS metadata: booktitle, volume 36, pages 46595--46623, publisher, and official proceedings URL. |
| `ChiangLee2023` | Updated ACL booktitle and added DOI `10.18653/v1/2023.acl-long.870`. |
| `Greshake2023` | Added ACM DOI `10.1145/3605764.3623985`. |
| `Zhan2024` | Updated ACL Findings booktitle; added pages 10471--10506, publisher, DOI `10.18653/v1/2024.findings-acl.624`, and ACL Anthology URL. |

## Checked With No Corrections Needed

- `Cello2002`
- `LandisKoch1977`
- `Fady2025report`
- `IBBIS2025`
- `Glassdoor2025`
- `Brown2020`

## Main Sources Used

- RAND report: https://www.rand.org/pubs/research_reports/RRA3329-1.html
- J. Craig Venter Institute report: https://www.jcvi.org/research/dna-synthesis-and-biosecurity-lessons-learned-and-options-future
- IBBIS legitimacy report PDF: https://ibbis.bio/wp-content/uploads/2024/02/IBBIS_Whitepaper_2024_Verifying_Customer_Legitimacy-1.pdf
- Applied Biosafety Wheeler et al. article: https://journals.sagepub.com/doi/10.1089/apb.2023.0034
- EU AI Act ELI page: https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
- European Biotech Act proposal page: https://health.ec.europa.eu/publications/proposal-regulation-establish-measures-strengthen-unions-biotechnology-and-biomanufacturing-sectors_en
- CLTR report page: https://www.longtermresilience.org/reports/cost-benefit-analysis-of-synthetic-nucleic-acid-screening-for-the-uk/
- HHS SynNA guidance PDF: https://aspr.hhs.gov/S3/Documents/SynNA-Guidance-2023.pdf
- IGSC Harmonized Screening Protocol PDF: https://genesynthesisconsortium.org/wp-content/uploads/IGSC-Harmonized-Screening-Protocol-v3.0-1.pdf
- Haddad article DOI: https://doi.org/10.1016/j.jemep.2025.101176
- Tan et al. PubMed record: https://pubmed.ncbi.nlm.nih.gov/33571426/
- Aclid site: https://www.aclid.bio/
- TwentyTwo site: https://www.twentytwo.bio/
- NeurIPS Zheng et al. proceedings page: https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html
- ACL Chiang and Lee page: https://aclanthology.org/2023.acl-long.870/
- Greshake et al. ACM DOI: https://doi.org/10.1145/3605764.3623985
- ACL Zhan et al. page: https://aclanthology.org/2024.findings-acl.624/
