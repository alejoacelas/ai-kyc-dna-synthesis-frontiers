# Evaluating AI-Assisted Customer Verification for DNA Synthesis Screening 

## Abstract

\[can be written last\]

We evaluated five large language models with web-search and with additional connected tools on five verification tasks that comprise the information-gathering phase of follow-up screening: verifying institutional affiliation, confirming institution type, checking email domain ownership, screening against sanctions lists, and identifying relevant background work. 

We compared AI performance against an expert human baseline on flag accuracy, source quality, source fidelity, and cost, using a database of plausible customers comprising life sciences researchers from around the world. Each researcher was screened in the context of a simulated order for a specific sequence of concern (SOC).

Based on our results, AI-assisted screening can be both cheaper and more accurate than manual screening when applied to customer screening tasks that focus on collecting and summarizing information. The best-performing model achieved higher accuracy than the human baseline at less than one hundredth of the cost. These results support piloting AI-assisted customer screening at DNA synthesis providers, with human reviewers in the loop retaining final authority over order fulfillment decisions.

## Introduction

Synthetic nucleic acids are unique among commercially available laboratory reagents and chemicals: they can be used to directly create pathogens through relatively simple laboratory practices and without the exogenous addition of a cultured organism. A vast majority of uses for synthetic nucleic acids positively benefit health and biological security (e.g. through biotechnological innovation or enabling molecular diagnostics). However, it is conceivable that a nefarious actor could purchase commercially available synthetic nucleic acids to cause harm. The sequences enabling them to do so are commonly referred to as “sequences of concern” (SOCs). Controlling access to synthetic nucleic acids is therefore a key biosecurity measure. 

As nucleic acid synthesis becomes cheaper and more accessible, strengthening safeguards against misuse becomes increasingly important. Organizations like the International Gene Synthesis Consortium (IGSC) have committed to two forms of screening practices that reduce misuse risk, namely sequence and customer screening, but widespread adoption remains limited (Crawford et al., 2024). A major barrier is cost: customer screening—particularly the follow-up verification triggered by potentially risky sequences—remains particularly expensive and labor-intensive (Carter and Friedman, 2015; Alexanian and Carter, 2024). For gene-length orders, recent work calculates a per-order cost of £0.95 for customer screening compared to only £0.10 for sequence screening–almost an order of magnitude difference ([Fady et al, 2025](https://www.longtermresilience.org/wp-content/uploads/2025/12/Cost-Benefit-Analysis-of-Synthetic-Nucleic-Acid-Screening-for-the-UK-Annexes-CLTR-2025.pdf)).

Currently, there is no single jurisdiction where providers of synthetic nucleic acids (“providers”) face an express mandate to undertake screening. While there are implied requirements for providers to do so based on existing anti-terror legislation (*inter alia*), these requirements are neither standardised across jurisdictions nor based on an internationally agreed risk framework. As a result, customer screening practices vary substantially across providers. This creates a heterogeneous risk profile across nations which undermines the strong collective security required to tackle self-amplifying biological threats which easily cross borders.  

Usually customer screening involves two phases: onboarding and follow-up screening. Onboarding checks verify basic customer information: name checks against watchlists, institutional affiliation, email domain ownership, and stated research purpose. After an order, sequence screening compares ordered sequences against databases of regulated pathogens to identify sequences of concern.

Follow-up screening is triggered when such sequences are detected and aims to determine whether a customer is a legitimate user of the ordered sequence. This often requires gathering information from multiple sources—publications, patents, institutional records—as well as back-and-forth communication with customers to obtain documentation such as proof of grant funding or institutional biosafety approval. The information-gathering component of customer screening is time-consuming but largely mechanical: it involves searching public records and rarely requires significant judgement calls. This makes it a promising target for AI assistance.

is triggered when such sequences are detected and aims to determine whether a customer is a legitimate user of the ordered sequence. This often requires gathering information from multiple sources—publications, patents, institutional records—and synthesizing it into a recommendation. is time-consuming but largely mechanical: it involves searching public records and rarely requires significant judgement calls. This makes it a promising target for AI assistance.

The aim of this study was to evaluate the potential uplift provided by AI tools in gathering information as part of the legitimate-use assessment process. We evaluated five large language models with web-search and with additional connected tools on five critical verification tasks that comprise the information-gathering phase of legitimate use assessment. 

We found that incorporating AI tools into the legitimate use assessment process reduces associated costs up to 500-fold (nearly 100-fold on average), while improving the accuracy of information gathered.   

## Methods

### ![][image1]

### Task Definition

We evaluate AI and human screeners on five verification tasks relevant to customer follow-up screening:

1. **Institutional affiliation verification**: Confirm the customer is currently affiliated with their claimed institution.  
2. **Institution type verification**: Confirm the institution is a legitimate biomedical research organization or company.  
3. **Email domain verification**: Confirm the customer's email domain belongs to their claimed institution.  
4. **Sanctions screening**: Check whether the customer or their institution appears on export control or sanctions lists.  
5. **Relevant work search**: Find publications, patents, or other work from the customer or their institution related to the ordered sequence.

For tasks 1–4, screeners assign a determination: flag (concern identified or information not found), no flag (verified without concern), or undetermined (insufficient evidence to decide). For task 5, screeners report relevant work without making a flag determination.

These tasks were selected because they can often be resolved using publicly available information, they appear in existing screening guidance (Alexanian and Carter, 2024), and they represent the information-gathering phase of follow-up screening rather than the judgment-intensive decision phase.

### Dataset

Our evaluation dataset comprises 134 customer profiles, each paired with a DNA synthesis order. Each profile includes the customer's name, institutional affiliation, email address, and a reference work (publication or patent) through which we identified them. The reference work serves as a point of comparison for whether screeners can find relevant background work.

Because human screening and manual grading of flag accuracy are time-intensive, we designated a 40-profile human baseline subset for these evaluations. Human screeners evaluated only this subset, and flag accuracy was manually graded only on these profiles. Automated metrics—source quality, source fidelity, and work relevance—were evaluated across the full 134-profile dataset.

To simulate realistic screening scenarios, we compiled profiles of researchers from publications and patents—some involving work on controlled pathogens, others on sequences that would not trigger screening concerns. We sampled across geographic regions and institutional types, and drew from the U.S. Consolidated Screening List (CSL), a government-maintained database of entities subject to export controls and sanctions, to include profiles that should trigger sanctions-related flags.

#### **Customer Categories**

We constructed four categories of customer profiles:

**Academic users of SOCs:** Life science researchers from academic institutions with documented laboratory work on SOCs.

**Industry users of SOCs:** Researchers at biotechnology or pharmaceutical companies with documented work, either personal or from their institution, on SOCs.

**CSL-affiliated academics:** Researchers at academic institutions appearing on the U.S. Consolidated Screening List, with documented work on SOCs.

**General life science researchers:** Researchers from academia and industry with documented laboratory work on typical non-SOC sequences: antibodies (scFv fragments), CAR-T constructs, common protein engineering targets, and diagnostic antigens.

All profiles in our dataset—including general life science researchers identified through non-SOC work—were assigned simulated orders from a standardized list of 22 SOC proteins. We selected proteins that would be reasonable to order for vaccine or therapeutics research while still being categorized as sequences of concern. \[Full list in Appendix A.\]

This means screeners encountered cases where researchers appeared to order SOCs without relevant background, a mismatch they were expected to identify and note.

#### **Collection Procedures**

**Academic researchers:** We searched Google Scholar using each sequence name as the primary search term. To promote geographic diversity, we appended names sampled from a random name generator weighted toward common names across world regions.

We selected publications meeting three criteria: (1) published after 2021, to increase the likelihood that affiliations remain current; (2) involving laboratory work on the target organism or protein, rather than purely computational or epidemiological analysis; and (3) plausibly requiring DNA synthesis, such as protein expression, cloning, or vaccine construct development. We filtered for authors with a publicly available email address or a confirmed institutional email domain listed on Google Scholar, ORCID, or other established research profile.

**Industry researchers:** We used two search strategies. For patent-based collection, we queried PatentScope using organism names, prioritizing patentees from outside the US and EU to encourage geographic diversity. We excluded large pharmaceutical firms, focusing instead on smaller companies that are harder to verify and more likely to require individual customer screening. 

For news-based collection, we searched on Google for articles combining organism names with terms like "vaccine," "diagnostics," and "startup," then identified researchers in laboratory roles at the surfaced companies via LinkedIn.

**CSL-affiliated academics:** We manually scanned entries in the U.S. Consolidated Screening List for institutions conducting biological research—primarily academic institutions in China, Russia, and Iran. We then searched Google Scholar using SOC organism names combined with institution names to find publications with authors at those institutions.

#### **Dataset Characteristics**

Table 1 summarizes the final dataset composition, showing statistics for both the full dataset and the human baseline subset. 

| Metric | Academics SOC | Industry SOC | General Life Sci. | CSL Academics | Total |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Total profiles | 56 (16) | 24 (11) | 29 (7) | 25 (7) | 134 (41) |
| Regional distribution |  |  |  |  |  |
| – US | 6 (2) | 8 (4) | 1 (0) | 0 (0) | 15 (6) |
| – Europe \+ Oceania | 18 (5) | 6 (2) | 4 (0) | 6 (0) | 34 (7) |
| – China | 8 (2) | 6 (3) | 19 (6) | 5 (1) | 38 (12) |
| – Other countries | 24 (7) | 4 (2) | 5 (1) | 14 (6) | 47 (16) |
| With institutional email domain | 49 (15) | 22 (10) | 18 (5) | 19 (3) | 108 (33) |

**Table 1:** Dataset composition by customer category. Numbers in parentheses indicate the 41-profile human baseline subset. Regional distribution based on institution location. Institutional email indicates profiles with business, academic, or government domains.

Only 81% of profiles (108/134) had email domains matching at least one stated institutional affiliation, as some researchers were affiliated with multiple institutions. This partly reflects regional conventions: for example, we found that researchers in China frequently list personal email domains rather than institutional addresses.

### Evaluation Subjects

#### **AI Models**

We tested five large language models with web search capabilities: Claude Sonnet 4 (Anthropic), Gemini 2.5 Pro (Google), Grok 4 (xAI), GLM 4.6 (Zhipu AI), and Minimax M2 (MiniMax). We selected models from major commercial providers and included GLM 4.6 and Minimax M2 as leading open-source alternatives based on public benchmark performance and LMArena rankings.

Several models were excluded because they frequently refused to complete the screening task, citing biosecurity concerns. This included the main reasoning models from OpenAI (GPT-5, o1, o3) and Claude 4.5 Sonnet from Anthropic.

Each model was tested under two conditions:

**Web search only:** Models had access to web search via Tavily, a search API designed for AI applications, and no other tools.

**Web search plus specialized tools:** Models had access to web search plus four additional tools:

* *Consolidated Screening List API:* Searches the U.S. government's consolidated list of sanctioned entities and restricted persons.  
* *Europe PMC:* Searches Europe PubMed Central for scientific articles by author, institution, topic, or ORCID identifier.  
* *ORCID profile:* Retrieves researcher profile information including affiliations, employment history, and recent publications.  
* *ORCID works search:* Searches a researcher's full ORCID publication list by keywords.

Both conditions used identical screening prompts. \[Full prompts in Appendix B.\]

#### **Human Baseline**

Two coauthors served as the human baseline: Kevin Flyangolts, founder of Aclid, a biosecurity platform for nucleic acid manufacturers; and Hanna Palya, a PhD student in mathematical epidemiology at the University of Warwick with prior publications on DNA synthesis screening.

Both evaluators were familiar with the research plan but received no task-specific training. They were given an earlier version of the screening instructions (developed in the process of optimizing prompts for model performance) and did not have previous access to the profiles they evaluated. They submitted responses through a custom interface that enforced the same output format as model responses.

The interface recorded snapshots of each screener's work at around 5 and 30 minutes. If they submitted a final answer earlier, that submission was used as the 30-minute snapshot. Each evaluator screened 20 customer profiles, for a total of 40 profiles in the human baseline subset. Profiles were randomly sampled from the full dataset with the constraint that no two shared the same reference work to encourage diversity.

We collected the 5-minute snapshot to estimate human performance under a time budget comparable to AI models, which averaged under 2 minutes per profile. However, responses at 5 minutes were typically incomplete, and this baseline underperformed AI models by a large margin. References to "human baseline" throughout the rest of this paper denote the 30-minute baseline unless otherwise noted.

### Evaluation Metrics

We evaluated each of the five verification tasks on three binary metrics, yielding 15 measurements per customer profile. To scale evaluation, we used Gemini 2.5 Flash in an LLM-as-a-judge setup for all metrics except flag accuracy, which was manually graded and only estimated for the human baseline subset. \[See evaluation prompts in Appendix C.\]

#### **Verification Tasks (Tasks 1–4)**

**Flag accuracy:** Whether the response's determination (flag, no flag, or undetermined) matches ground truth. Ground truth was established for the 40-profile human baseline subset through manual review of all model and human responses. When responses disagreed, we reviewed justifications and occasionally followed cited sources to verify claims. We were not blind to which screener produced each response, but none of the screeners participating in the human baseline were involved for ground truth annotation.

**Source quality:** Whether cited sources meet standards for independent verification. A source is acceptable if it exists independently of the customer and has editorial oversight. Acceptable sources include government registries, peer-reviewed publications, patent filings, regulatory submissions, business registrations, and established research profile aggregators. Unacceptable sources include LinkedIn profiles, personal websites, Wikipedia, and social media sites. A response passes this metric if all cited sources are acceptable; responses citing any unacceptable source, or no sources at all, fail.

**Source fidelity:** Whether factual claims are directly supported by cited sources. A claim fails if the source contradicts it, no source provides relevant information, or it presents speculation as established fact. Claims reporting absence of evidence (e.g., "no matching records found") passed by default, as it was often difficult to provide sources for them. Empty responses automatically failed.

#### **Background Work Task (Task 5\)**

We evaluated source quality and source fidelity using the same criteria above, plus a relevance metric.

**Work relevance:** Whether the response identifies work at least as relevant as the reference work used to include the customer in our dataset. Relevance is scored 0–5 based on three factors:

* *Proximity to customer:* Work authored by the customer directly (higher) versus produced by their institution (lower).  
* *Organism proximity:* Same organism as the order (higher), closely related organism (middle), or unrelated (lower).  
* *Laboratory involvement:* Hands-on experimentation (higher) versus purely computational work (lower).

A response passes if at least one retrieved source scores at or above the relevance level of the reference work used to identify the customer when creating our customer dataset.

### Prompt Development

We used the same task prompts across all models and developed them through iterative refinement on 10 customer profiles. After each iteration, we reviewed outputs for common errors such as citing unrelated sources, making overly broad claims, failing to search multiple sources before concluding information was unavailable, and incomplete compliance with sequential instructions. We rewrote and consolidated instructions multiple times to improve task adherence. \[See task prompts in Appendix B.\]

Evaluation prompts underwent a similar iterative process to improve alignment with human judgment. To validate the LLM-as-judge approach, one author independently re-graded a sample of 135 evaluation outputs blind to the original model grades. Agreement reached 83%, compared to 63% expected by chance (Cohen's κ \= 0.63). This falls within the "substantial agreement" range (0.61–0.80) on the Landis & Koch (CITE) interpretation scale. \[See evaluation prompts in Appendix C.\]

#### **Cost and Time Measurement**

**AI costs:** We calculated costs based on each provider's per-token API pricing, which priced input and output tokens separately. Web search queries cost $0.08 per query using the Tavily search provider. 

**Human costs:** We estimated costs based on time required and hourly wage for comparable roles. Using advertised salaries for customer service positions at large DNA synthesis providers \[[CITE](https://www.glassdoor.com/Salary/Twist-Bioscience-Customer-Service-Representative-Salaries-E925103_D_KO17,48.htm)\], we estimate each hour of work from a human screener costs around $54.

**Response time:** We record the wall-clock time from when the customer record is presented until response submission. Processing delays in the human baseline interface occasionally resulted in recorded response times being off by up to a minute.

## Results

### Metrics Aggregate Pass Rate

![][image2]

**Figure 1:** Pass rates by screener and metric on the 40-profile human baseline subset. Darker shading indicates higher pass rate.

As Figure 1 shows, for each metric other than flag accuracy, all evaluated models had a higher pass rate than the human baseline at either the 5-minute or 30-minute snapshot. Even for flag accuracy, the 30-minute human baseline beat only two of the ten model configurations studied.

The 5-minute human baseline performed much worse than any other screener setup, largely because responses recorded at that snapshot were practically always incomplete, leading to automatic failures on evaluation metrics.

Pass rates did not vary substantially across models. The best-performing model (Gemini with access to specialized tools) passed 89.8% of tests on the human baseline subset, while the worst-performing model (Gemini with only web search) passed 83.7%.

Access to specialized tools (Consolidated Screening List API, Europe PMC, ORCID) produced a modest but consistent accuracy improvement compared to web-search-only configurations. The improvement was most pronounced for sanctions screening, where the Consolidated Screening List API provided direct access to authoritative data otherwise available only through downloadable files or specialized interfaces.

\[Discuss why work relevance scores are lower with all tools\]

### Cost Comparison

All AI models produced customer reports faster and more cheaply than either human baseline. The most expensive model tested (Claude Sonnet 4\) was roughly 40 times cheaper than 30-minute human screening, while the cheapest configuration (MiniMax M2 with tools) was approximately 400 times cheaper.

| Model | Mean Cost (USD) | Mean Response Time |
| ----- | ----- | ----- |
| **Human baseline** |  |  |
| Human baseline (5 min) | $5.43 | 6.0 minutes |
| Human baseline (30 min) | $14.04 | 15.6 minutes |
| **AI models (all tools)** |  |  |
| Claude Sonnet 4 | $0.324 | 1.5 minutes |
| Grok 4 | $0.112 | 2.6 minutes |
| Gemini 2.5 Pro | $0.051 | 1.3 minutes |
| GLM 4.6 | $0.059 | 1.7 minutes |
| Minimax M2 | $0.033 | 2.2 minutes |
| *Average across AI models (all tools)* | *$0.116* | *1.9 minutes* |
| **AI models (web-only)** |  |  |
| Claude Sonnet 4 | $0.343 | 1.0 minutes |
| Grok 4 | $0.128 | 2.7 minutes |
| Gemini 2.5 Pro | $0.058 | 1.3 minutes |
| GLM 4.6 | $0.094 | 1.4 minutes |
| Minimax M2 | $0.059 | 2.5 minutes |
| *Average across AI models (web-only)* | *$0.136* | *1.8 minutes* |

**Table 2:** Per-customer screening costs and response times for the 40-profile human baseline subset. Human baseline costs are estimated at $54/hour based on DNA synthesis provider customer service salaries. AI costs include API token pricing and web search queries; other tools were cost-free.

Across AI models, cost per customer barely correlated with overall pass rates (R2 \= 0.013). The best-performing model, Gemini 2.5 Pro with access to all tools, was also the second cheapest model configuration. While the open-source models (GLM 4.6 and MiniMax M2) had per-token prices 2–8× lower than Gemini 2.5 Pro, additional web search queries and higher token consumption (often from extra tool calls) eliminated any meaningful cost advantage.

![][image3]

**Figure 3:** Average screening costs per customer against the overall pass rate across all four metrics on the complete customer dataset.

Even with substantially cheaper AI models, per-customer costs are driven by web search queries. For the model with the lowest price per token (Minimax M2), web search costs averaged 60% of the total cost for processing a customer. Alternative web search providers—including custom tools offered by some AI model developers—could reduce costs further, but the lack of standardization of such tools demands additional efforts in adapting prompts and source extraction to obtain good results. 

### Flag Error Analysis

​​We manually reviewed a random sample of 126 flag errors across all screeners and assigned each to one of five categories:

* **Criterion Deviation:** The screener's flag determination conflicted with the criteria used to decide the ground truth flag. These criteria were often specified explicitly in the screening prompt, though some frequent edge cases were not addressed directly and required interpretation.  
* **Search Failure:** The screener did not locate information that was central to the flag determination but that other screeners successfully found.  
* **Missing Response:** The screener produced no response in the relevant field, the response was incomplete or not formatted according to task instructions.  
* **Ambiguous Case:** The screener had access to all relevant information, but no clear rule in the flag determination criteria resolved the case. These situations required judgment calls where reasonable screeners might disagree.  
* **Source Misinterpretation:** The screener cited appropriate sources but misrepresented their content, leading to an incorrect flag.

#### **Error Distribution**

Table X summarizes error category distributions across screener types.

| Error Category | Example | Human Baseline | AI (All Tools) | AI (Web Only) | Overall |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Criterion Deviation | Flagging a biology department as "not biomedical" because its university appears on a sanctions list | 35% (6) | 39% (19) | 42% (25) | 40% (50) |
| Search Failure | Missing that a researcher moved to a different academic institution | 35% (6) | 35% (17) | 17% (10) | 26% (33) |
| Missing Response | Empty response field or abruptly terminated output | 18% (3) | 20% (10) | 23% (14) | 21% (27) |
| Ambiguous Case | Email domain matches recently outdated company domain | 12% (2) | 6% (3) | 15% (9) | 11% (14) |
| Source Misinterpretation | Assuming connections between nearby organizations without evidence | 0% (0) | 0% (0) | 2% (1) | 1% (1) |

The frequency of each error type was similar across screeners. Criterion deviation was the most common category, accounting for 39.7% of all errors. On inspection, a small number of recurring patterns accounted for the majority of mistakes in this category, such as not flagging personal email addresses from otherwise reputable Chinese researchers.

Because grading flags required substantial manual work, we only graded them after settling on the final prompts provided to human and AI models. We expect that including explicit guidance addressing these specific cases could substantially reduce criterion deviation errors for both AI and human screeners. 

Search failure was the next most common error type. Notably, web-only models had a lower rate (16.7%) than AI models with access to specialized tools or human screeners. \[TODO: explain this later with the stats on tool use by model\]

Missing responses accounted for 21.4% of errors. For human screeners, these typically arose from deliberate decisions to skip a criterion—for example, skipping remaining checks after confirming a customer's institution appears on a sanctions list—that coincided with a flag error. For AI models, missing responses often resulted from outputs that did not adhere to the requested table format or, occasionally, from extraction failures when parsing model responses.

Ambiguous cases and source misinterpretation were least common, accounting for 11.1% and 0.8% of errors respectively. Ambiguous cases typically involved conflicting or partial evidence that made it difficult to establish clear ground truth. Source misinterpretation was rare despite the fact that around 15% of criterion descriptions contained some factual inaccuracy, as measured by the source fidelity metric. Most of these inaccuracies were minor and did not affect the final flag determination.

**Geographic Variation**

Error rates varied by customer region. European customers had the highest pass rates, potentially reflecting better documentation in English-language sources. Chinese customers showed higher false negative rates on domain verification, as screeners often selected not to flag otherwise reputable customers that appeared with a personal email domain. They also showed higher false positive rates on sanctions screening. US customers showed unexpectedly high affiliation verification errors, but we didn't perceive any consistent pattern looking at the full response transcripts.

![][image4]

**Figure 6:** Flag accuracy error rates averaged for all AI models by task and customer region on the human baseline subset.

## Discussion

### Interpreting results

We evaluated AI models with web-search only and AI models with additional connected tools on follow-up screening of customers who ordered sequences of concern against a human baseline. While our evaluation took place outside of a DNA synthesis company, we attempted to simulate real customers going through a plausible screening workflow. The observations we made warrant piloting AI-aided customer screening in DNA synthesis companies and possibly other providers with similar risk profiles (e.g., cloud labs and pathogen repositories). This fits with existing screening guidelines that pair sequence screening with customer screening and recommend follow-up screening when an order is flagged.

Overall, AI models were more accurate than the 30-minute human baseline. However, we spent more time on creating and refining prompts than we did on instructing humans. High-context human screeners might outperform current models on the hardest cases, when domain context and judgment are needed. This performance pattern reflects how current LLMs are trained and finetuned. Instruction-tuned models are explicitly optimized to follow written instructions (including via reinforcement learning from human feedback), which makes them good at executing checklists and structured procedures when the guidance is clear. In contrast, they do not reliably "learn on the job" across cases during deployment, unless an explicit update mechanism (e.g., fine-tuning or continual-learning methods) is implemented. This kind of adaptation is non-trivial and can lead to failures, like forgetting the previous task when learning a new one. Thus, our approach of finding clear customer-screening guidance and encoding it in a stable prompt, along with explicit rules for acceptable sources and quality of claims is the better option for now.

Performance varied more on source quality than on flag accuracy. While there was little difference between models and the 30-minute human baseline in flag pass rates, there was greater variability in the pass rate for sources and free-text claims. For example, Claude performed particularly badly on providing sources for the institution's type, while the human baseline performed best here. For providing background work claims, Grok with all tools did the best, and the human baseline did worst. The 5-minute human baseline severely underperformed compared to all the models and the 30-minute human baseline, as five minutes was insufficient to do many of the tasks. In contrast, AI queries (whether with all tools or web-only) took between 1.8 and 1.9 minutes to complete. This demonstrates a major advantage of AI-enabled KYC tools: enhanced throughput and the ability to handle more queries per unit time. As the synthetic nucleic acid market is projected to grow with a compound annual growth rate of \~15% (Fady et al, 2025b), enabling tools to scale will be a key contribution of AI to biosecurity.

Access to specialized tools provided modest but consistent improvements. Overall, the “all tools” version of models had slightly higher pass rates but this varied between tasks and models. The all-tools versions of models performed consistently better than the web-search tools only in the sanctions check task. This is because sanctions lists are mostly only available through APIs or as downloadable material and not as webpages. Financial services use API-based sanctions screening as standard practice, like Sanctions.io and Dilisense. In our design, we only queried the US Consolidated Screening List, but many more lists could be added for better coverage.

### Implications for Screening Practice

The mix of tasks performed here could plausibly be part of one customer screening instance, but they could also be split into onboarding tasks and follow-up tasks. Crucially, the “ship/follow-up/not-ship” decision should remain in the hands of humans. We caution against the development of AI tools leveraging a “human-out-of-the-loop” (HOOTL) design until such time as any biases in large language models has been addressed. Early implementation of HOOTL systems could result in innovation being stifled through autonomous AI judgments on legitimate use, and this in a potentially inequitable way.

Speeding up the screening task, or in other words, cost reduction, is the main reason AI-aided KYC is worth piloting in DNA synthesis companies. The cheapest model to run coincided with the best performing model based on pass rates \- this was the all-tool version of Gemini with $0.051/response. We estimate our human baseline to cost $14, based on the median customer service rep base pay at one of the largest DNA providers. This is a more than 500-fold reduction in costs of these specific tasks. Open-sourced tools that perform these tasks, like Cliver, could therefore aid the efforts of providers who already screen, and incentivize those who do not yet. For-profit tools also have legitimacy here, which could help drive the adoption of customer screening, especially if they are coupled with profit-making products.

Onboarding tasks (or customer verification tasks) normally include checking customer name against government watchlists, requesting institutional affiliation, checking for institutional email and physical address and requesting whether the product is for research purposes, prior to screening the ordered sequence. Follow-up tasks have a wider range: the goal of these is to collect as much relevant information about the customer as needed (or as possible) for determining whether the customer is a legitimate user of the ordered sequence. Many of these are tasks that require requesting additional information, like institutional oversight, from customers and then checking the information given. The “checking” tasks lend themselves well to automation, while “requesting” tasks rely on human interaction.

Several approaches can reduce the workload of “requesting” tasks. Policy recommendations include whitelisting customers who are legitimate for a set of SOCs, and re-checking this legitimacy every year or so but not at every order. Another solution could be to frontload as much of plausibly necessary information as possible. IBBIS has created templates for this, so when a customer knows that they are ordering an SOC (which they should, given that they need the appropriate BSL lab for it), they can provide more information that's necessary for screening. This way, more of the request tasks can be turned into check tasks, which can then be sped up by using LLMs. Crucially, the ultimate decision whether to ship the order will need to remain with a human.

### Limitations

Any information gathering system can only be as good as the information available to it. Screening accuracy depends on the extent to which publicly available information exists about the customer. The pass rate of both LLMs and humans on the evaluated tasks depends on this, and this is an inherent limitation of any information-gathering endeavour. Using AI in KYC should still help in some cases of difficult-to-interpret data, like when large chunks of the customer's information is in a different language from the provider's operating language. However, this dependence on public information could introduce bias. The quick assessment of well-documented customers could bias against fulfilling the orders of harder-to-assess customers, some of whom will be researchers from low-income countries, who have lower access to biotechnology to begin with.

Beyond the general limitation of only containing researchers who have *some* internet presence, our evaluation dataset likely overrepresents well-documented researchers. By design, all profiles in our dataset have discoverable publications, patents, or institutional affiliations—information necessary both for constructing realistic profiles and for screeners to verify them. This likely overrepresents established researchers relative to the typical DNA synthesis customer base, which includes laboratory technicians, students, and industry personnel with minimal publication records. Stealth startups, early career researchers and people working at universities with limited online presence will have less data that can be evaluated automatically and so these instances of screening will remain reliant on personal contact. Performance on our benchmark may overestimate real-world accuracy for these customers.

## Conclusion

This work builds on years of guidance on DNA synthesis customer screening. We evaluated how commercially available and open-source LLMs perform on customer screening tasks outlined by Carter et al. and are present in various screening guidances. We propose a human-in-the-loop approach, where AI models check the provided information against public records and summarize findings, and humans request additional information and make decisions about fulfilling the order. We included our prompt in the appendix, which should be easy to tailor to the specific needs of DNA providers and other relevant biotechnology companies. The code for this paper, and for the open source AI-KYC tool Cliver, are available on GitHub. The authors of this paper are keen to help implement any pilots involving these systems.