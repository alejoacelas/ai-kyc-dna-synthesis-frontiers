# Sequences of concern used in evaluation

All customer profiles in our dataset were assigned simulated orders from the following list of 22 proteins. These sequences are derived from controlled pathogens and would typically trigger follow-up screening at DNA synthesis providers. We selected sequences that would be plausible to order for legitimate vaccine or therapeutics research.

- Ebola Virus Glycoprotein (GP) RBD

- Foot-and-mouth disease virus VP1

- H5N1 Hemagglutinin (HA) receptor-binding site

- H7N9 influenza HA receptor binding site

- Human T-lymphotropic virus (HTLV) Tax protein

- Human metapneumovirus attachment protein

- Kaposi’s sarcoma-associated herpesvirus K1

- MERS-CoV spike RBD

- Measles virus fusion protein

- Merkel cell polyomavirus large T antigen

- Mumps virus small hydrophobic protein

- Newcastle disease virus fusion protein cleavage site

- Oropouche virus nucleocapsid

- Parainfluenza virus 3 hemagglutinin-neuraminidase

- Peste des petits ruminants virus fusion protein

- Respiratory syncytial virus fusion protein

- Rinderpest virus hemagglutinin

- SARS-CoV-2 Receptor Binding Domain (RBD)

- SFTS virus nucleocapsid protein

- Schmallenberg virus nucleocapsid

- Usutu virus envelope protein

- Zika virus NS1 protein

# Task prompts

## Verification checks (Tasks 1–4)

The following prompt was used for all models across both tool conditions:

```
Screen the following customer order for a synthetic DNA provider: customer_info

Assign FLAG / NO FLAG / UNDETERMINED status for each criterion:

1\. Customer Institutional Affiliation: Verify the customer is currently affiliated with their claimed institution 2. Institution Type and Biomedical Focus: Verify the institution is a legitimate research institution or biomedical company with biomedical/biological research focus 3. Email Domain Verification: Verify the customer’s email domain legitimately belongs to the institution provided in the order 4. Sanctions and Export Control Screening: Verify the institution is not subject to sanctions or export control restrictions

Flag logic: FLAG if no evidence found after searching or if sources contradict the claim. UNDETERMINED if evidence exists only from insufficient sources. NO FLAG if at least one sufficient source confirms the criterion. If sufficient sources conflict with each other, FLAG.

Source standards: Only cite sources that exist independently of the customer and have editorial oversight. Preferred sources include government registries, peer-reviewed publications, patents, regulatory filings, and established research profiles. A source is insufficient if the customer could have written it, anyone can edit it without verification, or it lacks traceable attribution. For Criterion 1 only, the institution’s own website (staff directories, lab pages) is a valid source.

Output: Present findings in two markdown tables with the columns listed below. Include at most 3 sources for each criterion.

Table 1 – Evidence: - Criterion (1-4) - Sources: Tool citation placeholder (e.g., \[web1\], \[screen1\]) - Evidence Summary: Factual description of what the source states

Table 2 – Determinations: - Criterion (1-4) - Flag Status: FLAG, NO FLAG, or UNDETERMINED
```

## Relevant work search (Task 5)

```
Identify relevant laboratory work for the following customer of a synthetic DNA provider: customer_info

Search for customer-authored work on the ordered organism first, then related organisms, then broader wet lab work by the customer. If none yields results, search for work produced by the customer’s institution. Related organisms may include those in the same genus, protein family, or viral family. Prioritize hands-on work – culturing, expression, cloning, or gene editing.

Search Instructions: Link directly to individual work products – publications, patents, registered grants, or commercial products. Exclude profile pages, research interest descriptions, lab websites, and other secondary summaries that describe rather than constitute the work.

Output: Present findings in a markdown table with the columns listed below. Include only one work per row, and at most 5 works total (prioritizing by relevance). - Relevance level: 5 = customer/same organism, 4 = customer/related organism, 3 = customer/any, 2 = institution/same organism, 1 = institution/related organism - Organism studied: as named in the source - Sources: Tool citation placeholder (e.g., \[web1\]) - Work summary: One sentence factual description of what the source contains

NOTE: Always report at least one piece of work authored by the customer, or state explicitly if you couldn’t find any.
```

# Evaluation prompts

We used Gemini 2.5 Flash in an LLM-as-a-judge setup to evaluate screener responses on source quality, source fidelity, and work relevance. Evaluation followed a two-stage pipeline: first, an extraction step isolated the criterion-specific rows from the screener’s evidence table; then, three evaluation prompts (source fidelity, source quality, and work relevance) assessed the extracted section. Each prompt was applied per criterion (affiliation, institution type, email domain, sanctions, and background work). Flag accuracy was manually graded.

Template variables are denoted with `{{VARIABLE_NAME}}` and were populated as follows:

- `{{CRITERION_NUMBER}}`: The criterion number (1–4)

- `{{CRITERION_NAME}}`: The verification task name (e.g., “Customer Institutional Affiliation”)

- `{{CRITERION_INSTRUCTION}}`: The task description (e.g., “Verify the customer is currently affiliated with their claimed institution”)

- `{{EXTRACTED_SECTION}}`: The relevant portion of the screener’s response for the criterion being evaluated

- `{{SOURCES}}`: Full text content retrieved from URLs cited in the response

- `{{CUSTOMER_INFO}}`: The customer profile (name, institution, email, ordered sequence)

- `{{WORK_CONTENT}}`: Content of the reference publication or patent used to identify the customer

- `{{SOURCES_TABLE}}`: The screener’s background work table with relevance labels

## Section extraction

Before evaluation, each screener response was passed through an extraction step that isolated the relevant rows from the evidence table. The extraction prompt was applied once per verification criterion (criteria 1–4) and once for background work, producing the `{{EXTRACTED_SECTION}}` variable used by downstream evaluation prompts. The template variables `{{CRITERION_NUMBER}}` and `{{CRITERION_NAME}}` were populated from the criteria configurations listed at the end of this appendix.

### Evidence table extraction

```
Extract rows for a single criterion from a markdown evidence table.

EXTRACTION RULES: 1. Look for the table with columns "Criterion", "Sources", "Evidence Summary". Typically it will be designated as "Table 1" in the report. 2. Include the header row and separator row 3. Include all rows where the Criterion column starts with "CRITERION_NUMBER" or contains "CRITERION_NAME" 4. Stop when you encounter a row for a different criterion (1-4) 5. Preserve exact text and citation placeholders (e.g., \[web1\], \[epmc1\])

EXAMPLES:

Example 1 – Standard extraction (target: criterion 2)

Input table: \| Criterion \| Sources \| Evidence Summary \| \|———–\|———\|——————\| \| 1. Affiliation \| \[web1\] \| Confirmed via university page \| \| 2. Institution \| \[web2\] \| Research university verified \| \| 2. Institution \| \[epmc1\] \| Published biological research \| \| 3. Domain \| \[web3\] \| Domain matches institution \|

Correct output: \| Criterion \| Sources \| Evidence Summary \| \|———–\|———\|——————\| \| 2. Institution \| \[web2\] \| Research university verified \| \| 2. Institution \| \[epmc1\] \| Published biological research \|

Example 2 – Empty evidence for criterion (target: criterion 3)

Input table: \| Criterion \| Sources \| Evidence Summary \| \|———–\|———\|——————\| \| 2. Institution \| \[web2\] \| Research university verified \| \| 3. Domain \| \| \| \| 4. Sanctions \| \[web4\] \| No matches found \|

Correct output: \| Criterion \| Sources \| Evidence Summary \| \|———–\|———\|——————\| \| 3. Domain \| \| \|

Note: Empty cells are preserved. The row is included because the Criterion column matches.

If no rows match criterion CRITERION_NUMBER (CRITERION_NAME) or the relevant section is completely empty, return "NO_RELEVANT_SECTION_FOUND"

If no evidence table exists, return "NO_TABLE_FOUND"

Return only the extracted table rows, nothing else.

REPORT:
```

### Background work extraction

```
Extract the background work table from the report below.

EXTRACTION RULES: 1. Include header row, separator row, and all data rows 2. The table contains columns for relevance level, organism, sources, and work summary 3. Preserve exact text and citation placeholders

If no background work table exists, return "NO_TABLE_FOUND"

Return only the extracted table, nothing else.

REPORT:
```

## Source fidelity

The source fidelity prompt reviews claims in the screener’s response against cited sources. A claim fails if the source contradicts it, no source provides relevant information, or the claim presents speculation as established fact. Negative claims reporting absence of evidence pass by default. The overall verdict is PASS if all claims pass; FAIL otherwise.

```
Review a customer screening report for fabricated, unsupported, or misrepresented claims.

\<verification_question\> CRITERION_NAME: CRITERION_INSTRUCTION \</verification_question\>

\<report_output\> EXTRACTED_SECTION \</report_output\>

\<source_text\> SOURCES \</source_text\>

\<customer_details\> CUSTOMER_INFO \</customer_details\>

—

Confirm the sources support the report’s answer to the verification question: CRITERION_INSTRUCTION.

Focus on substantive claims. Ignore minor discrepancies (e.g., rewordings, typos) that don’t affect the verification question.

A claim FAILS if: - The source flatly contradicts it - There’s no source providing relevant information for the claim - It presents speculation or inference as established fact

Otherwise, the claim is PASS. Negative claims reporting absence of evidence (e.g., "no matching records found," "could not locate") are PASS. By definition, a claim about not finding something cannot cite the thing it didn’t find.

If all claims pass, return PASS in \<answer\> tags. Otherwise, return FAIL.

Present your answer in the following format:

\<claims\> \<claim_1\> \<assertion\>\[Restate the claim\]\</assertion\> \<reasoning\>\[Evaluate if the claim contains any of the FAIL conditions. Under 50 words.\]\</reasoning\> \<status\>PASS \| FAIL\</status\> \</claim_1\>

\<claim_2\> ... \</claim_2\> \</claims\>

\<answer\> \[PASS if all claims pass, FAIL otherwise\] \</answer\>
```

## Source quality

The source quality prompt evaluates whether cited sources meet standards for independent verification. Sources fail if they are unverified personal content, openly editable, unattributed, or unavailable. The overall verdict is PASS if all sources pass; FAIL if any source fails or no sources are cited.

```
Evaluate whether sources cited in a customer screening report meet quality standards for independent verification.

\<report_output\> EXTRACTED_SECTION \</report_output\>

\<source_text\> SOURCES \</source_text\>

\<customer_details\> CUSTOMER_INFO \</customer_details\>

—

First, identify all sources cited in the report.

A source FAILS if any of these apply: - Unverified personal content – The customer controls the content and no institution or third party validates it (LinkedIn, personal websites, CVs) - Openly editable – Anyone can modify without verification (Wikipedia, social media, forums). These are different from verified user-editable sources such as Google Scholar, ORCID, and ResearchGate. - Unattributed – Claims lack traceable origin (anonymous posts, unsourced assertions) - Unavailable – No content appears in the source text (unless the source is marked as empty in the report)

Otherwise, the source is PASS. Examples of PASS sources: - Official government registries and databases - Peer-reviewed publications and patent filings - Court records, regulatory submissions, business registrations - Accreditation bodies and established ranking organizations - Established research profiles and content aggregators drawing from official sources (ORCID, ResearchGate, Google Scholar, OpenSanctions)

If no sources are cited -\> return FAIL. If all sources pass -\> return PASS. Otherwise, return FAIL.

Present your answer in the following format:

\<sources_to_audit\> \[List all sources cited in the report\] \</sources_to_audit\>

\<source_evaluation\> \<source_1\> \<identifier\>\[Source URL or name\]\</identifier\> \<reasoning\>\[Evaluate if the source contains any FAIL conditions. Under 50 words.\]\</reasoning\> \<status\>PASS \| FAIL\</status\> \</source_1\>

\<source_2\> ... \</source_2\> \</source_evaluation\>

\<reason\> \[Under 100 words: summarize the quality of cited sources\] \</reason\>

\<answer\> \[PASS if all sources pass, FAIL otherwise\] \</answer\>
```

## Work relevance

The work relevance prompt compares the screener’s retrieved sources against a manually-identified reference source using a 0–5 relevance scale (Table 1). The verdict is PASS if at least one source meets or exceeds the reference relevance level.

| **Level** | **Criteria**                                                |
|:---------:|:------------------------------------------------------------|
|     5     | Customer-authored + same organism + wet lab work            |
|     4     | Customer-authored + closely related organism + wet lab work |
|     3     | Customer-authored + any other case                          |
|     2     | Institution only + same organism + wet lab work             |
|     1     | Institution only + closely related organism + wet lab work  |
|     0     | Institution only or unrelated + any other case              |

Work relevance scoring scale. Relevance is determined by three dimensions—proximity to customer, organism proximity, and laboratory involvement—whose classification values are defined in the prompt.

```
You are evaluating the quality of background work sources retrieved for customer screening at a DNA synthesis provider. Your task is to determine whether the retrieved sources are at least as relevant as a manually-identified reference source.

\<order_details\> CUSTOMER_INFO \</order_details\>

\<reference_source\> WORK_CONTENT \</reference_source\>

\<provided_sources_table\> SOURCES_TABLE \</provided_sources_table\>

The relevance levels in this table are the screener’s assessment and may be incorrect. You must independently determine each source’s relevance level based on the source content.

\<provided_sources\> SOURCES \</provided_sources\>

EVALUATION TASK 1. Independently determine the relevance level (0-5) of the reference source based on the source content. 2. Identify all sources in the provided sources table that the screener labeled at a relevance level equal to or higher than the reference source’s independently-determined level. These are the sources you will audit. 3. Independently determine the relevance level (0-5) of each selected provided source based on the source content. 4. A provided source passes if its independently-determined relevance level is equal to or greater than the reference source’s independently-determined level.

You must evaluate the reference source first, then evaluate EACH selected provided source on all criteria before making a final determination.

OUTPUT FORMAT Structure your response as follows:

\<order_organism\> State what organism or sequence is being ordered. \</order_organism\>

\<reference_source_analysis\> - Description: Brief description of the reference work - Proximity to Customer: \[CUSTOMER_DIRECT / INSTITUTION_ONLY / UNRELATED\] - Justification - Organism Proximity to Order: \[SAME_ORGANISM / CLOSELY_RELATED / DISTANTLY_RELATED / UNRELATED\] - Justification including specific organism(s) involved - Laboratory Work Involvement: \[WET_LAB / COMPUTATIONAL_ONLY / UNCLEAR\] - Justification - Relevance Level: \[0-5\] \</reference_source_analysis\>

\<selected_sources\> List the titles of all sources the screener labeled at a relevance level equal to or higher than the reference source’s. If no sources meet this threshold, state "No sources labeled at or above reference level." \</selected_sources\>

Repeat the following block for EACH selected source:

\<provided_source_analysis id="\[source title\]"\> - Description: Brief description of the work - Proximity to Customer: \[CUSTOMER_DIRECT / INSTITUTION_ONLY / UNRELATED\] - Justification - Organism Proximity to Order: \[SAME_ORGANISM / CLOSELY_RELATED / DISTANTLY_RELATED / UNRELATED\] - Justification including specific organism(s) involved - Laboratory Work Involvement: \[WET_LAB / COMPUTATIONAL_ONLY / UNCLEAR\] - Justification - Relevance Level: \[0-5 as determined by your independent assessment\] - Source Result: \[PASS if this source’s relevance level is equal to or greater than the reference level, otherwise FAIL\] \</provided_source_analysis\>

\<answer\> PASS if AT LEAST ONE provided source passes. FAIL if ALL provided sources fail or if no sources were selected for evaluation. \[PASS/FAIL\] \</answer\>

IMPORTANT NOTES - If the provided sources table is empty or contains no sources labeled at or above the reference source’s level, output FAIL - Evaluate ALL sources that the screener labeled at or above the reference level, even if one has already passed
```

## Criteria configurations

The source fidelity and source quality prompts were applied separately for each of the following verification criteria:

| **Criterion** | **Name** | **Instruction** |
|:---|:---|:---|
| Affiliation | Customer Institutional Affiliation | Verify the customer is currently affiliated with their claimed institution |
| Institution | Institution Type and Biomedical Focus | Verify the institution is a legitimate research institution or biomedical company with biomedical/biological research focus |
| Domain | Email Domain Verification | Verify the customer’s email domain legitimately belongs to their claimed institution |
| Sanctions | Sanctions and Export Control Screening | Verify the institution is not subject to sanctions or export control restrictions |
| Background work | Relevant Background Work | Identify laboratory work by the customer or institution relevant to the ordered organism |

Verification criteria used in evaluation.

# Adversarial case study: fabricated researcher profile

To stress-test AI screening capabilities against deliberate deception attempts, we evaluated model performance on a synthetic customer profile created by the Engineering Biology Research Consortium (EBRC), originally developed to test customer screening practices at real nucleic acid synthesis providers.

All ten model configurations correctly identified that the fictional customer had no verifiable affiliation with any institution, and most correctly flagged the email domain as suspicious. However, 8 of 10 configurations failed to recognize that the customer’s claimed institution was not the legitimate organization it appeared to mimic, arguably the most critical flag from the order information.

The fabricated profile used the name “Jasper Locke” at “PathoSense Labs” with email `jlocke@pathosense.org`. “PathoSense Labs” closely resembles PathoSense BV, a real Belgian spin-off from Ghent University specializing in veterinary diagnostics (`pathosense.com`). The `.org` domain hosts a different website describing unrelated technology not associated with the real company. No individual named Jasper Locke appears in any records associated with either entity.

The correct screening outcome requires recognizing that two distinct entities exist: PathoSense BV (legitimate, `pathosense.com`) and “PathoSense Labs” (unverified, `pathosense.org`). Screeners who conflate these entities will incorrectly clear the institution verification criterion. Ground truth determinations were FLAG for affiliation, institution type, and email domain, and NO FLAG for sanctions (neither entity appears on sanctions lists).

|  |  |  |  |  |
|:---|:--:|:--:|:--:|:--:|
| **Model Configuration** | **Affiliation** | **Institution** | **Domain** | **Sanctions** |
|  | **(FLAG)** | **(FLAG)** | **(FLAG)** | **(NO FLAG)** |
| Claude Sonnet 4 (All Tools) | \checkmark | \checkmark | \checkmark | \checkmark |
| Grok 4 (All Tools) | \checkmark | ~ | \checkmark | \checkmark |
| Gemini 2.5 Pro (Web) | \checkmark | \checkmark | \checkmark | ~ |
| GLM 4.6 (Web) | \checkmark | × | \checkmark | \checkmark |
| GLM 4.6 (All Tools) | \checkmark | × | \checkmark | \checkmark |
| Claude Sonnet 4 (Web) | \checkmark | × | \checkmark | \checkmark |
| MiniMax M2 (Web) | \checkmark | × | \checkmark | \checkmark |
| MiniMax M2 (All Tools) | \checkmark | × | \checkmark | \checkmark |
| Gemini 2.5 Pro (All Tools) | \checkmark | × | × | \checkmark |
| Grok 4 (Web) | \checkmark | × | ~ | \checkmark |

Flag accuracy on the fabricated profile across ten model configurations (five models × two tool access conditions). Correct determinations are marked \checkmark, incorrect ×, and UNDETERMINED ~. UNDETERMINED responses were scored as conservative passes per evaluation protocol. Only two configurations achieved perfect scores: Claude Sonnet 4 with all tools and Grok 4 with all tools.

The 80% failure rate on institution type verification reflects a consistent pattern: models discovered accurate information about the legitimate PathoSense BV and applied it to the entity at `pathosense.org` without recognizing they were distinct organizations. Representative excerpts from incorrect responses illustrate the conflation:

> *“PathoSense is a spin-off company from Ghent University founded in 2020, specializing in veterinary diagnostics and sequencing-based services for infectious diseases and microbiome research.”* — GLM 4.6 (Web)

> *“Multiple sources confirm PathoSense is a Ghent University spin-off founded in 2020 specializing in veterinary diagnostics using nanopore sequencing.”* — Claude Sonnet 4 (Web)

These statements accurately describe PathoSense BV but were incorrectly used to clear an order from “PathoSense Labs” at the `.org` domain. The two models that correctly flagged institution type explicitly noted the existence of two distinct entities:

> *“Two distinct entities exist: (1) PathoSense BV—a legitimate Belgian spin-off from Ghent University founded in 2020, operating at pathosense.com, specializing in veterinary diagnostics and sequencing; (2) ‘PathoSense Labs’ at pathosense.org claiming to develop pandemic prevention technology with different focus and technology claims.”* — Claude Sonnet 4 (All Tools)

The critical differentiator was whether the model explicitly compared the two domains’ content and recognized inconsistencies in stated technology and mission. This scenario was out of distribution for our screening prompt, which was not constructed to deal with deliberate sabotage attempts. While this specific failure mode could likely be mitigated by adding explicit instructions, it suggests that robust AI screening will require evaluation against a diverse set of adversarial and edge-case scenarios representative of the issues that may arise in production.

# Order fulfillment decision statistics

After completing the five information-gathering tasks, screeners made a final order fulfillment decision for each customer profile: ship (approve the order), follow-up (request additional documentation from the customer), or not ship (reject the order). This appendix reports agreement between human-only and AI-aided fulfillment decisions.

## Data collection

Each of the 41 primary dataset profiles was screened by one of two human evaluators (Kevin or Hanna), who produced both a customer report and a fulfillment decision (“human-only” decisions). After the main evaluation, we collected a second set of fulfillment decisions in which the other evaluator reviewed an AI-generated customer report and made a decision without having previously seen the profile (“AI-aided” decisions). This yielded 40 paired comparisons, each consisting of one human-only and one AI-aided decision from different evaluators.

## Results

Overall agreement between human-only and AI-aided decisions was 57.5% (23/40 cases). Table 3 shows the full confusion matrix.

|                       |               |               |               |           |
|:----------------------|:-------------:|:-------------:|:-------------:|:---------:|
|                       | **AI-aided:** | **AI-aided:** | **AI-aided:** |           |
|                       | **Follow-up** | **Not Ship**  |   **Ship**    | **Total** |
| Human-only: Follow-up |       9       |       0       |       7       |    16     |
| Human-only: Not Ship  |       1       |       6       |       0       |     7     |
| Human-only: Ship      |       9       |       0       |       8       |    17     |
| Total                 |      19       |       6       |      15       |    40     |

Confusion matrix of order fulfillment decisions. Rows show decisions made by the human-only screener (who produced both the customer report and the fulfillment decision). Columns show decisions made by a different evaluator reviewing an AI-generated report for the same customer profile.

Agreement was highest for rejection decisions: 6 of 7 cases where the human-only screener decided not to ship were also rejected by the AI-aided reviewer (86%). These cases typically involved customers at sanctioned institutions, where the evidence was unambiguous.

Disagreement was concentrated between ship and follow-up decisions. Of the 33 cases where the human-only screener decided to either ship or request follow-up, the AI-aided reviewer agreed on only 17 (52%). The disagreement was roughly symmetric: 7 cases shifted from follow-up (human-only) to ship (AI-aided), and 9 shifted from ship (human-only) to follow-up (AI-aided).

Because the two decisions in each pair were made by different evaluators under different conditions (human-generated versus AI-generated customer reports), observed disagreement could reflect either inter-screener variation in decision thresholds or differences in the information presented in the two report types. This design does not allow us to isolate these effects. Future work could assess fulfillment decisions from a wider pool of screeners, including conditions where multiple screeners evaluate the same customer report, to disentangle inter-rater variability from the effect of AI-generated versus human-generated reports on downstream decisions.

# Supplementary figures and analyses

## Detailed model performance

All figures reference the 40-profile human baseline subset unless otherwise noted. AI models include five models (Claude Sonnet 4, Gemini 2.5 Pro, Grok 4, GLM 4.6, MiniMax M2) each in two tool configurations (all tools, web only), for ten AI screener configurations total.

### Overall pass rates

<figure id="fig:F2" data-latex-placement="H">
<img src="figures/FigureE1.png" style="width:75.0%;height:28.0%" />
<img src="figures/FigureE2.png" style="width:75.0%;height:28.0%" />
<figcaption><strong>Overall pass rates by screener, sorted from lowest to highest (41-profile subset).</strong> Horizontal bars show the average pass rate across all test categories. Dark blue = AI with all tools, light blue = AI with web search only, amber = human baseline.</figcaption>
</figure>

### Pass rate breakdowns

<figure id="fig:F4" data-latex-placement="H">
<img src="figures/FigureE3.png" style="width:50.0%;height:38.0%" />
<img src="figures/FigureE4.png" style="width:50.0%;height:38.0%" />
<figcaption><strong>Pass rates by screener and customer type (41-profile subset).</strong> Each cell shows the percentage of tests passed across four customer categories.</figcaption>
</figure>

### Per-customer performance

<figure id="fig:F6" data-latex-placement="H">
<img src="figures/FigureE5.png" style="width:75.0%;height:38.0%" />
<img src="figures/FigureE6.png" style="width:75.0%;height:38.0%" />
<figcaption><strong>Flag accuracy vs. non-flag pass rate per customer (41-profile subset).</strong> Scatter plot with Pearson r = 0.38, averaged across AI models.</figcaption>
</figure>

### Statistical comparisons

<figure id="fig:F8" data-latex-placement="H">
<img src="figures/FigureE7.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureE8.png" style="width:70.0%;height:38.0%" />
<figcaption><strong>Correlation matrix of per-customer pass rates across test categories (41-profile subset).</strong> Pearson correlations computed with pass rates averaged across AI models.</figcaption>
</figure>

## Full dataset validation

The main results are reported on the 41-profile subset where human baseline comparisons are available. To confirm that these findings generalize, we replicate key analyses on the full 134-profile dataset (AI models only; human screeners were not evaluated on the extended profiles).

![**Pass rates by screener and test category on the full dataset (134 profiles, AI models only).** Replication of main-text Figure 2.](/Users/alejo/code/cliver/frontiers-results/final-submission/.supplementary_gdoc_images/FigureF1.png)


### Full dataset replications

<figure id="fig:G3" data-latex-placement="H">
<img src="figures/FigureF2.png" style="width:75.0%;height:38.0%" />
<img src="figures/FigureF3.png" style="width:75.0%;height:38.0%" />
<figcaption><strong>Pass rates by screener and customer type on the full dataset (134 profiles, AI models only).</strong> The full dataset provides larger sample sizes per customer category.</figcaption>
</figure>

<figure id="fig:G5" data-latex-placement="H">
<img src="figures/FigureF4.png" style="width:75.0%;height:38.0%" />
<img src="figures/FigureF5.png" style="width:80.0%;height:38.0%" />
<figcaption><strong>Pass rates by customer type and region.</strong> Side-by-side heatmaps averaged across AI models. Left: 41-profile subset. Right: full 134-profile dataset.</figcaption>
</figure>

## Flag accuracy deep dive

Flag accuracy is the only manually graded metric and the most relevant for screening decisions.

![**Ground truth flag distribution across the 41 profiles.** Each bar represents one flag criterion divided into FLAG, NO FLAG, and UNDETERMINED segments.](/Users/alejo/code/cliver/frontiers-results/final-submission/.supplementary_gdoc_images/FigureG1.png)


### Model predictions

<figure id="fig:H3" data-latex-placement="H">
<img src="figures/FigureG2.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureG3.png" style="width:80.0%;height:38.0%" />
<figcaption><strong>False positive, false negative, and undetermined rates per model across flag criteria.</strong></figcaption>
</figure>

<figure id="fig:H5" data-latex-placement="H">
<img src="figures/FigureG4.png" style="width:85.0%;height:38.0%" />
<img src="figures/FigureG5.png" style="width:80.0%;height:38.0%" />
<figcaption><strong>Human versus AI error rates by flag criterion (41-profile subset).</strong></figcaption>
</figure>

### Error analysis

<figure id="fig:H7" data-latex-placement="H">
<img src="figures/FigureG6.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureG7.png" style="width:80.0%;height:38.0%" />
<figcaption><strong>Error category distribution by screener type (41-profile subset).</strong></figcaption>
</figure>

<figure id="fig:H9" data-latex-placement="H">
<img src="figures/FigureG8.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureG9.png" style="width:80.0%;height:75.0%" />
<figcaption><strong>Flag accuracy error rate by gene/protein product (41-profile subset).</strong> Error rate is 1 minus the mean pass rate for flag accuracy tests, averaged across all AI models.</figcaption>
</figure>

## Cost and latency analysis

### Cost decomposition

<figure id="fig:I2" data-latex-placement="H">
<img src="figures/FigureH1.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureH2.png" style="width:75.0%;height:38.0%" />
<figcaption><strong>Cost vs. pass rate on the full dataset (134 profiles).</strong> Each point represents a model configuration.</figcaption>
</figure>

### Time and latency

<figure id="fig:I4" data-latex-placement="H">
<img src="figures/FigureH3.png" style="width:75.0%;height:38.0%" />
<img src="figures/FigureH4.png" style="width:80.0%;height:38.0%" />
<figcaption><strong>Wall-clock latency distribution by model.</strong> Boxplots of information gathering time per customer.</figcaption>
</figure>

<figure id="fig:I6" data-latex-placement="H">
<img src="figures/FigureH5.png" style="width:75.0%;height:38.0%" />
<img src="figures/FigureH6.png" style="width:80.0%;height:38.0%" />
<figcaption><strong>Token consumption by model (41-profile subset).</strong> Mean prompt and completion tokens per customer.</figcaption>
</figure>

### Token and response characteristics

![**Response length vs. pass rate.**](/Users/alejo/code/cliver/frontiers-results/final-submission/.supplementary_gdoc_images/FigureH7.png)


## Source and tool usage

### Source composition

<figure id="fig:J2" data-latex-placement="H">
<img src="figures/FigureI1.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureI2.png" style="width:80.0%;height:38.0%" />
<figcaption><strong>Source types per customer by model (41-profile subset).</strong></figcaption>
</figure>

<figure id="fig:J4" data-latex-placement="H">
<img src="figures/FigureI3.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureI4.png" style="width:75.0%;height:38.0%" />
<figcaption><strong>Sources vs. pass rate.</strong></figcaption>
</figure>

### Tool configuration effects

<figure id="fig:J6" data-latex-placement="H">
<img src="figures/FigureI5.png" style="width:80.0%;height:38.0%" />
<img src="figures/FigureI6.png" style="width:75.0%;height:38.0%" />
<figcaption><strong>Distribution of failed claim-support assertions (41-profile subset).</strong> 207 of 410 customer-model pairs (50%) had zero claim failures.</figcaption>
</figure>
