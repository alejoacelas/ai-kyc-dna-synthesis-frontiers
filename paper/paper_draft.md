## Abstract

\[can be written last\]

## 

## Introduction

As nucleic acid synthesis becomes cheaper and more accessible, strengthening safeguards against misuse becomes increasingly important. Organizations like the International Gene Synthesis Consortium (IGSC) have committed to two forms of screening practices that reduce misuse risk, namely sequence and customer screening, but widespread adoption remains limited (Crawford et al., 2024). A major barrier is cost: customer screening—particularly the follow-up verification triggered by potentially risky sequences—remains particularly expensive and labor-intensive (Carter and Friedman, 2015; Alexanian and Carter, 2024).

While customer screening practices vary substantially across providers, they often involve two phases: onboarding and follow-up screening. Onboarding checks verify basic customer information: name checks against watchlists, institutional affiliation, email domain ownership, and stated research purpose. Follow-up screening, triggered when orders contain sequences of concern, aims to determine whether a customer is a legitimate user of the ordered sequence. This often requires gathering information from multiple sources—publications, patents, institutional records—and synthesizing it into a recommendation. The information-gathering component of customer screening is time-consuming but largely mechanical: it involves searching public records and rarely requires significant judgement calls. This makes it a promising target for AI assistance.

We evaluated five large language models with web-search and with additional connected tools on five verification tasks that comprise the information-gathering phase of follow-up screening: verifying institutional affiliation, confirming institution type, checking email domain ownership, screening against sanctions lists, and identifying relevant background work. 

We compared AI performance against an expert human baseline on flag accuracy, source quality, source fidelity, and cost, using a database of plausible customers comprising life sciences researchers from around the world. Each researcher was screened in the context of a simulated order for a specific sequence of concern (SOC).

Based on our results, AI-assisted screening can be both cheaper and more accurate than manual screening when applied to customer screening tasks that focus on collecting and summarizing information. The best-performing model achieved higher accuracy than the human baseline at less than one hundredth of the cost. These results support piloting AI-assisted customer screening at DNA synthesis providers, with human reviewers in the loop retaining final authority over order fulfillment decisions.

## Methods

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

Our evaluation dataset comprises 134 synthetic customer profiles representing plausible DNA synthesis orders. Each profile includes the customer's name, institutional affiliation, email address, and a reference work (publication or patent) through which we identified them. The reference work serves as a point of comparison for whether screeners can find relevant background work.

#### **Customer Categories**

We constructed four categories of customer profiles:

**Academics with SOC background (n=56):** Life science researchers from academic institutions with documented laboratory work on sequences of concern (SOCs).

**Industry researchers with SOC background (n=24):** Researchers at biotechnology or pharmaceutical companies with documented work, either personal or from their institution, on SOCs.

**CSL-affiliated academics (n=25):** Researchers at academic institutions appearing on the U.S. Consolidated Screening List, with documented work on SOCs.

**General life science researchers (n=31):** Researchers from academia and industry with documented laboratory work on sequences that would not trigger screening concerns.

All profiles were assigned orders from a standardized list of 22 proteins derived from controlled pathogens, regardless of the customer's actual research background. This means general life science researchers receive orders outside their documented expertise—cases where screeners should not find directly relevant background work.

#### **Sequence Selection**

For SOC orders, we compiled proteins that would be reasonable to order for vaccine or therapeutics research and that are categorized as sequences of concern. \[Full list in Appendix A.\]

For the general life science category, we selected sequences representative of typical orders that would not trigger screening concerns: antibodies and immunoproteins (e.g., scFv fragments, nanobodies), CAR-T constructs, classic protein engineering targets (e.g., TEM-1 beta-lactamase, cytochrome P450 BM3), and diagnostic antigens.

#### **Collection Procedures**

**Academic researchers:** We searched Google Scholar using each sequence name as the primary search term. To promote geographic diversity, we appended names sampled from a random name generator weighted toward common names across world regions.

We selected publications meeting three criteria: (1) published after 2021, to increase the likelihood that affiliations remain current; (2) involving laboratory work on the target organism or protein, rather than purely computational or epidemiological analysis; and (3) plausibly requiring DNA synthesis, such as protein expression, cloning, or vaccine construct development. We filtered for authors with a publicly available email address or a confirmed institutional email domain listed on Google Scholar, ORCID, or other established research profile.

**Industry researchers:** We used two search strategies. For patent-based collection, we queried PatentScope using organism names, prioritizing patentees from outside the US and EU and manually excluding large pharmaceutical firms. For news-based collection, we searched on Google for articles combining organism names with terms like "vaccine," "diagnostics," and "startup," then identified researchers in laboratory roles at the surfaced companies via LinkedIn.

**CSL-affiliated academics:** We manually scanned entries in the U.S. Consolidated Screening List for institutions conducting biological research—primarily academic institutions in China, Russia, and Iran. We then searched Google Scholar using SOC organism names combined with institution names to find publications with authors at those institutions.

#### **Dataset Characteristics**

Table 1 summarizes the final dataset composition.

| Metric | Academics (SOC) | Industry (SOC) | General Life Sci. | CSL Academics | Total |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Total profiles | 56 | 24 | 29 | 25 | 134 |
| **Regional distribution** |  |  |  |  |  |
| – US | 6 | 8 | 1 | 0 | 15 |
| – Europe \+ Oceania | 18 | 6 | 4 | 6 | 34 |
| – China | 8 | 6 | 19 | 5 | 38 |
| – Other | 24 | 4 | 5 | 14 | 47 |
| With institutional email domain | 49 | 22 | 18 | 19 | 108 |

**Table 1:**  Dataset composition by customer category. Regional distribution based on institution location. Institutional email indicates profiles with business, academic, or government domains.

Only 81% of profiles (108/134) had email domains matching at least one stated institutional affiliation, as some researchers were affiliated with multiple institutions. This partly reflects regional conventions: for example, researchers in China frequently list personal email domains rather than institutional addresses.

### Evaluation Subjects

#### **AI Models**

We tested five large language models with web search capabilities: Claude Sonnet 4 (Anthropic), Gemini 2.5 Pro (Google), Grok 4 (xAI), GLM 4.6 (Zhipu AI), and Minimax M2 (MiniMax). We selected models from major commercial providers and included GLM 4.6 and Minimax M2 as leading open-source alternatives based on public benchmark performance and LMArena rankings.

Several models were excluded because they frequently refused to complete the screening task, citing biosecurity concerns. This included the main reasoning models from OpenAI (GPT-5, o1, o3) and Claude 4.5 Sonnet from Anthropic.

Each model was tested under two conditions:

**Web search only:** Models had access to web search via Tavily and no other tools.

**Web search plus specialized tools:** Models had access to web search plus four additional tools:

* *Consolidated Screening List API:* Searches the U.S. government's consolidated list of sanctioned entities and restricted persons.  
* *Europe PMC:* Searches Europe PubMed Central for scientific articles by author, institution, topic, or ORCID identifier.  
* *ORCID profile:* Retrieves researcher profile information including affiliations, employment history, and recent publications.  
* *ORCID works search:* Searches a researcher's full ORCID publication list by keywords.

Both conditions used identical screening prompts. \[Full prompts in Appendix B.\]

#### **Human Baseline**

Two coauthors served as the human baseline: Kevin Flyangolts, founder of Aclid, a biosecurity platform for nucleic acid manufacturers; and Hanna Palya, a PhD student in mathematical epidemiology at the University of Warwick with prior publications on DNA synthesis screening.

Both evaluators were familiar with the research plan but received no task-specific training. They were given an earlier version of the screening instructions (developed in the process of optimizing prompts for model performance) and did not have previous access to the profiles they evaluated. They submitted responses through a custom interface that enforced the same output format as model responses.

The interface recorded snapshots of each screener's work at 5 and 30 minutes. If they submitted a final answer earlier, that submission was used as the 30-minute snapshot. Each evaluator screened 20 customer profiles, for a total of 40 profiles in the human baseline subset. Profiles were randomly sampled from the full dataset with the constraint that no two shared the same reference work to encourage diversity.

### Evaluation Metrics

We evaluated each of the five verification tasks on three binary metrics, yielding 15 measurements per customer profile. To scale evaluation, we used Gemini 2.5 Flash in an LLM-as-a-judge setup for all metrics except flag accuracy, which was manually graded and only estimated for the human baseline subset. \[See evaluation prompts in Appendix C.\]

#### **Verification Tasks (Tasks 1–4)**

**Flag accuracy:** Whether the response's determination (flag, no flag, or undetermined) matches ground truth. Ground truth was established for the 40-profile human baseline subset through manual review of all model and human responses. When responses disagreed, we reviewed justifications and occasionally followed cited sources to verify claims. We were not blind to which screener produced each response, but none of the screeners participating in the human baseline were involved for ground truth annotation.

**Source quality:** Whether cited sources meet standards for independent verification. A source passes if it exists independently of the customer and has editorial oversight. Sources explicitly indicated as acceptable included government registries, peer-reviewed publications, patent filings, regulatory submissions, business registrations, and established research profile aggregators. Sources marked as unacceptable included LinkedIn profiles, personal websites, Wikipedia, or social media sites. Responses citing no sources automatically failed.

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

Evaluation prompts underwent a similar process to improve alignment with human judgment.

#### **Cost and Time Measurement**

**AI costs:** We calculated costs based on each provider's per-token API pricing, which priced input and output tokens separately. Web search queries cost $0.08 per query using the Tavily search provider. 

**Human costs:** We estimated costs based on time required and hourly wage for comparable roles. Using advertised salaries for customer service positions at large DNA synthesis providers \[[CITE](https://www.glassdoor.com/Salary/Twist-Bioscience-Customer-Service-Representative-Salaries-E925103_D_KO17,48.htm)\], we estimate each hour of work from a human screener costs around $54.

**Response time:** We record the wall-clock time from when the customer record is presented until response submission. Processing delays in the human baseline interface occasionally resulted in recorded response times being off by up to a minute.

## Results

### Metrics Aggregate Pass Rate

![][image1]

**Figure 1:** Pass rates by screener and metric on the 40-profile human baseline subset. Darker shading indicates higher pass rate.

As Figure 1 shows, for each metric other than flag accuracy, all evaluated models had a higher pass rate than the human baseline at either the 5-minute or 30-minute snapshot. Even for flag accuracy, the 30-minute human baseline beat only two of the ten model configurations studied.

The 5-minute human baseline performed much worse than any other screener setup, largely because responses recorded at that snapshot were practically always incomplete, leading to automatic failures on evaluation metrics.

Pass rates did not vary substantially across models. The best-performing model (Gemini with access to specialized tools) passed 89.8% of tests on the human baseline subset, while the worst-performing model (Gemini with only web search) passed 83.7%.

![][image2]

**Figure 2:** Average pass rates by screener on the human baseline subset.

Access to specialized tools (Consolidated Screening List API, Europe PMC, ORCID) produced a modest but consistent accuracy improvement compared to web-search-only configurations. The improvement was most pronounced for sanctions screening, where the Consolidated Screening List API provided direct access to authoritative data otherwise available only through downloadable files or specialized interfaces.

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
| **AI models (web-only)** |  |  |
| Claude Sonnet 4 | $0.343 | 1.0 minutes |
| Grok 4 | $0.128 | 2.7 minutes |
| Gemini 2.5 Pro | $0.058 | 1.3 minutes |
| GLM 4.6 | $0.094 | 1.4 minutes |
| Minimax M2 | $0.059 | 2.5 minutes |

**Table 2:** Per-customer screening costs and response times for the 40-profile human baseline subset. Human baseline costs are estimated at $54/hour based on DNA synthesis provider customer service salaries. AI costs include API token pricing and web search queries; other tools were cost-free.

Across AI models, cost per customer barely correlated with overall pass rates (R2 \= 0.013). The best-performing model, Gemini 2.5 Pro with access to all tools, was also the second cheapest model configuration. While the open-source models (GLM 4.6 and MiniMax M2) had per-token prices 2–8× lower than Gemini 2.5 Pro, additional web search queries and higher token consumption (often from extra tool calls) eliminated any meaningful cost advantage.

![][image3]

**Figure 3:** Average screening costs per customer against the overall pass rate across all four metrics on the complete customer dataset.

Even with substantially cheaper AI models, per-customer costs are bounded by web search queries. For the model with the lowest price per token (Minimax M2), web search costs averaged 60% of the total cost for processing a customer. Alternative web search providers—including custom tools offered by some AI model developers—could reduce costs further, but the lack of standardization of such tools demands additional efforts in adapting prompts and source extraction to obtain good results. 

### Flag Error Analysis

![][image4]

**Figure 4:** Error rates by flag accuracy criterion comparing human baseline (30 min) with highest and lowest error rates from AI models. \[ADD ERROR CLASSIFICATION FIGURE ONCE DATA IS COMPUTED\]

We reviewed failing test cases to characterize what benchmark errors represent in practice. Errors fell into three categories:

**Category A (X%):** \[Description\]

**Category B (Y%):** \[Description\]

**Category C (Z%):** \[Description\]

These patterns suggest that human screeners with targeted training would likely improve. However, the comparison reflects a realistic deployment scenario: organizations investing in AI screening would optimize prompts before deployment, just as they would train human screeners.

**Geographic Variation**

Error rates varied by customer region. European customers had the highest pass rates, potentially reflecting better documentation in English-language sources. Chinese customers showed higher false negative rates on domain verification, as screeners often selected not to flag otherwise reputable customers that appeared with a personal email domain. They also showed higher false positive rates on sanctions screening. US customers showed unexpectedly high affiliation verification errors, but we didn't perceive any consistent pattern looking at the full response transcripts.

![][image5]

**Figure 6:** Flag accuracy error rates averaged for all AI models by task and customer region on the human baseline subset.

## Discussion

### Interpreting results

We evaluated AI models with web-search only and AI models with additional connected tools on follow-up screening of customers who ordered sequences of concern against a human baseline. While our evaluation took place outside of a DNA synthesis company, we attempted to simulate real customers going through a plausible screening workflow. The observations we made warrant piloting AI-aided customer screening in DNA synthesis companies and possibly other providers with similar risk profiles (e.g., cloud labs and pathogen repositories). This fits with existing screening guidelines that pair sequence screening with customer screening and recommend follow-up screening when an order is flagged.

Overall, AI models were more accurate than the 30-minute human baseline. However, we spent more time on creating and refining prompts than we did on instructing humans. High-context human screeners might outperform current models on the hardest cases, when domain context and judgment are needed. This performance pattern reflects how current LLMs are trained and finetuned. Instruction-tuned models are explicitly optimized to follow written instructions (including via reinforcement learning from human feedback), which makes them good at executing checklists and structured procedures when the guidance is clear. In contrast, they do not reliably "learn on the job" across cases during deployment, unless an explicit update mechanism (e.g., fine-tuning or continual-learning methods) is implemented. This kind of adaptation is non-trivial and can lead to failures, like forgetting the previous task when learning a new one. Thus, our approach of finding clear customer-screening guidance and encoding it in a stable prompt, along with explicit rules for acceptable sources and quality of claims is the better option for now.

Performance varied more on source quality than on flag accuracy. While there was little difference between models and the 30-minute human baseline in flag pass rates, there was greater variability in the pass rate for sources and free-text claims. For example, Claude performed particularly badly on providing sources for the institution's type, while the human baseline performed best here. For providing background work claims, Grok with all tools did the best, and the human baseline did worst. The 5-minute human baseline severely underperformed compared to all the models and the 30-minute human baseline, as five minutes was insufficient to do many of the tasks.

Access to specialized tools provided modest but consistent improvements. Overall, the all tools version of models had slightly higher pass rates but this varied between tasks and models. The all-tools versions of models performed consistently better than the web-search tools only in the sanctions check task. This is because sanctions lists are mostly only available through APIs or as downloadable material and not as webpages. Financial services use API-based sanctions screening as standard practice, like Sanctions.io and Dilisense. In our design, we only queried the US Consolidated Screening List, but many more lists could be added for better coverage.

### Implications for Screening Practice

The mix of tasks performed here could plausibly be part of one customer screening instance, but they could also be split into onboarding tasks and follow-up tasks. Crucially, the ship/follow-up/not-ship decision should remain in the hands of humans.

Speeding up the screening task, or in other words, cost reduction, is the main reason AI-aided KYC is worth piloting in DNA synthesis companies. The cheapest model to run coincided with the best performing model based on pass rates \- this was the all-tool version of Gemini with $0.051/response. We estimate our 30-minute human baseline to cost $14, based on the median customer service rep base pay at one of the largest DNA providers. This is a more than 500-fold reduction in costs of these specific tasks. Open-sourced tools that perform these tasks, like Cliver, could therefore aid the efforts of providers who already screen, and incentivize those who do not yet. For-profit tools also have legitimacy here, which could help drive the adoption of customer screening, especially if they are coupled with profit-making products.

The mix of tasks performed here could plausibly be part of one customer screening instance, but they could also be split into onboarding tasks and follow-up tasks. Onboarding tasks (or customer verification tasks) normally include checking customer name against government watchlists, requesting  institutional affiliation, checking for institutional email and physical address and requesting whether the product is for research purposes, prior to screening the ordered sequence. Follow-up tasks have a wider range: the goal of these is to collect as much relevant information about the customer as needed (or as possible) for determining whether the customer is a legitimate user of the ordered sequence. Many of these are tasks that require requesting additional information, like institutional oversight, from customers and then checking the information given. The “checking” tasks lend themselves well to automatization, while “requesting” tasks rely on human interaction.

Several approaches can reduce the  workload of “requesting” tasks. Policy recommendations include whitelisting customers who are legitimate for a set of SOCs, and re-checking this legitimacy every year or so but not at every order. Another solution could be to frontload as much of plausibly necessary information as possible. IBBIS has created templates for this, so when a customer knows that they are ordering an SOC (which they should, given that they need the appropriate BSL lab for it), they can provide more information that's necessary for screening. This way, more of the request tasks can be turned into check tasks, which can then be sped up by using LLMs. Crucially, the ultimate decision whether to ship the order will need to remain with a human.

### Limitations

Screening accuracy depends on the extent of publicly available information about the customer. The pass rate of both LLMs and humans on the evaluated tasks depends on this, and this is an inherent limitation of any information-gathering endeavour. Using AI in KYC should still help in some cases of difficult-to-interpret data, like when large chunks of the customer's information is in a different language from the provider's operating language. However, this dependence on public information could introduce bias. The quick assessment of well-documented customers could bias against fulfilling the orders of harder-to-assess customers, some of whom will be researchers from low-income countries, who have lower access to biotechnology to begin with.

Beyond the general limitation of only containing researchers who have *some* internet presence, our evaluation dataset likely overrepresents well-documented researchers. By design, all profiles in our dataset have discoverable publications, patents, or institutional affiliations—information necessary both for constructing realistic profiles and for screeners to verify them. This likely overrepresents established researchers relative to the typical DNA synthesis customer base, which includes laboratory technicians, students, and industry personnel with minimal publication records. Stealth startups, early career researchers and people working at universities with limited online presence will have less data that can be evaluated automatically and so these instances of screening will remain reliant on personal contact. Performance on our benchmark may overestimate real-world accuracy for these customers.

## Conclusion

This work builds on years of guidance on DNA synthesis customer screening. We evaluated how commercially available and open-source LLMs perform on customer screening tasks outlined by Carter et al. and are present in various screening guidances. We propose a human-in-the-loop approach, where AI models check the provided information against public records and summarize findings, and humans request additional information and make decisions about fulfilling the order. We included our prompt in the appendix, which should be easy to tailor to the specific needs of DNA providers and other relevant biotechnology companies. The code for this paper, and for the open source AI-KYC tool Cliver, are available on GitHub. The authors of this paper are keen to help implement any pilots involving these systems.

## Appendix A

* Ebola Virus Glycoprotein (GP) RBD  
* Foot-and-mouth disease virus VP1  
* H5N1 Hemagglutinin (HA) receptor-binding site  
* H7N9 influenza HA receptor binding site  
* Human T-lymphotropic virus (HTLV) Tax protein  
* Human metapneumovirus attachment protein  
* Kaposi's sarcoma-associated herpesvirus K1  
* MERS-CoV spike RBD  
* Measles virus fusion protein  
* Merkel cell polyomavirus large T antigen  
* Mumps virus small hydrophobic protein  
* Newcastle disease virus fusion protein cleavage site  
* Oropouche virus nucleocapsid  
* Parainfluenza virus 3 hemagglutinin-neuraminidase  
* Peste des petits ruminants virus fusion protein  
* Respiratory syncytial virus fusion protein  
* Rinderpest virus hemagglutinin  
* SARS-CoV-2 Receptor Binding Domain (RBD)  
* SFTS virus nucleocapsid protein  
* Schmallenberg virus nucleocapsid  
* Usutu virus envelope protein  
* Zika virus NS1 protein