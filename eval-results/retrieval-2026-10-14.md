# Retrieval evaluation

*2026-10-14 · embedder `FastEmbedEmbedder (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)` · knowledge base 467 chunks · 57 labelled questions (+3 out-of-scope, not scored here)*

Hit@k = a provision that contains the answer is among the top k results. MRR = mean reciprocal rank (depth 10). Gold labels were assigned by reading the source text.

## Overall

| Method | n | Hit@1 | Hit@3 | Hit@5 | MRR (95% CI) | Superseded text returned |
|---|---|---|---|---|---|---|
| vector only | 57 | 42% | 67% | 72% | 0.559 (0.46–0.66) | 0% |
| keyword only (FTS) | 57 | 26% | 44% | 51% | 0.373 (0.28–0.48) | 0% |
| hybrid (RRF) | 57 | 49% | 63% | 74% | 0.589 (0.48–0.70) | 0% |
| hybrid + rerank (lexical) | 57 | 54% | 72% | 81% | 0.648 (0.54–0.75) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) | 57 | 60% | 82% | 84% | 0.702 (0.60–0.80) | 0% |

## By language

| Method / group | n | Hit@1 | Hit@3 | Hit@5 | MRR (95% CI) | Superseded text returned |
|---|---|---|---|---|---|---|
| vector only — **en** | 40 | 42% | 68% | 72% | 0.555 (0.43–0.68) | 0% |
| vector only — **mr** | 17 | 41% | 65% | 71% | 0.568 (0.38–0.74) | 0% |
| keyword only (FTS) — **en** | 40 | 20% | 42% | 52% | 0.335 (0.22–0.45) | 0% |
| keyword only (FTS) — **mr** | 17 | 41% | 47% | 47% | 0.465 (0.26–0.68) | 0% |
| hybrid (RRF) — **en** | 40 | 48% | 65% | 78% | 0.585 (0.46–0.71) | 0% |
| hybrid (RRF) — **mr** | 17 | 53% | 59% | 65% | 0.598 (0.38–0.80) | 0% |
| hybrid + rerank (lexical) — **en** | 40 | 57% | 75% | 80% | 0.674 (0.55–0.79) | 0% |
| hybrid + rerank (lexical) — **mr** | 17 | 47% | 65% | 82% | 0.587 (0.39–0.77) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) — **en** | 40 | 65% | 85% | 88% | 0.744 (0.62–0.85) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) — **mr** | 17 | 47% | 76% | 76% | 0.605 (0.41–0.80) | 0% |

## By topic

| Method / group | n | Hit@1 | Hit@3 | Hit@5 | MRR (95% CI) | Superseded text returned |
|---|---|---|---|---|---|---|
| vector only — **consumer** | 9 | 56% | 89% | 89% | 0.698 (0.47–0.93) | 0% |
| vector only — **other** | 6 | 83% | 83% | 83% | 0.850 (0.55–1.00) | 0% |
| vector only — **rti** | 42 | 33% | 60% | 67% | 0.488 (0.37–0.60) | 0% |
| keyword only (FTS) — **consumer** | 9 | 33% | 56% | 78% | 0.487 (0.25–0.74) | 0% |
| keyword only (FTS) — **other** | 6 | 33% | 83% | 83% | 0.528 (0.25–0.81) | 0% |
| keyword only (FTS) — **rti** | 42 | 24% | 36% | 40% | 0.327 (0.21–0.45) | 0% |
| hybrid (RRF) — **consumer** | 9 | 56% | 78% | 89% | 0.676 (0.43–0.92) | 0% |
| hybrid (RRF) — **other** | 6 | 100% | 100% | 100% | 1.000 (1.00–1.00) | 0% |
| hybrid (RRF) — **rti** | 42 | 40% | 55% | 67% | 0.512 (0.37–0.63) | 0% |
| hybrid + rerank (lexical) — **consumer** | 9 | 33% | 78% | 78% | 0.556 (0.33–0.80) | 0% |
| hybrid + rerank (lexical) — **other** | 6 | 100% | 100% | 100% | 1.000 (1.00–1.00) | 0% |
| hybrid + rerank (lexical) — **rti** | 42 | 52% | 67% | 79% | 0.617 (0.48–0.74) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) — **consumer** | 9 | 56% | 89% | 89% | 0.704 (0.46–0.93) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) — **other** | 6 | 67% | 100% | 100% | 0.833 (0.67–1.00) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) — **rti** | 42 | 60% | 79% | 81% | 0.684 (0.55–0.80) | 0% |

## By question style

| Method / group | n | Hit@1 | Hit@3 | Hit@5 | MRR (95% CI) | Superseded text returned |
|---|---|---|---|---|---|---|
| vector only — **colloquial** | 12 | 25% | 42% | 50% | 0.401 (0.21–0.63) | 0% |
| vector only — **direct** | 45 | 47% | 73% | 78% | 0.601 (0.49–0.72) | 0% |
| keyword only (FTS) — **colloquial** | 12 | 8% | 17% | 17% | 0.166 (0.04–0.35) | 0% |
| keyword only (FTS) — **direct** | 45 | 31% | 51% | 60% | 0.429 (0.32–0.55) | 0% |
| hybrid (RRF) — **colloquial** | 12 | 33% | 42% | 50% | 0.410 (0.19–0.67) | 0% |
| hybrid (RRF) — **direct** | 45 | 53% | 69% | 80% | 0.637 (0.52–0.76) | 0% |
| hybrid + rerank (lexical) — **colloquial** | 12 | 33% | 42% | 58% | 0.426 (0.21–0.67) | 0% |
| hybrid + rerank (lexical) — **direct** | 45 | 60% | 80% | 87% | 0.707 (0.60–0.82) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) — **colloquial** | 12 | 33% | 58% | 67% | 0.465 (0.24–0.70) | 0% |
| hybrid + rerank (jina-reranker-v2-base-multilingual) — **direct** | 45 | 67% | 89% | 89% | 0.766 (0.67–0.87) | 0% |

## Misses of the best method (hybrid + rerank (jina-reranker-v2-base-multilingual)): not in top 3

* **q10** Can a PIO refuse to give information because it is personal information?  
  expected one of `rti-act-2005-en-s8, judg-girish-deshpande` · got `rti-act-2005-en-s9, rti-act-2005-en-s20, rti-act-2005-en-s10` · rank 4
* **q16** Which information must a public authority publish on its own without being asked?  
  expected one of `rti-act-2005-en-s4` · got `rti-act-2005-mr-p60, rti-act-2005-mr-p28, rti-act-2005-mr-p63` · rank >10
* **q17** Who can ask for information under the RTI Act?  
  expected one of `rti-act-2005-en-s3, rti-act-2005-en-s2` · got `rti-act-2005-en-s6, rti-act-2005-en-s18, rti-act-2005-en-s7` · rank >10
* **q21** Is information free for a person below the poverty line?  
  expected one of `rti-act-2005-en-s7, rti-rules-2012-central` · got `rti-act-2005-mr-p16, rti-act-2005-en-s20, rti-act-2005-en-s10` · rank >10
* **q24** Is the office of the Chief Justice of India covered by the RTI Act?  
  expected one of `judg-subhash-agarwal` · got `rti-act-2005-en-s2, rti-act-2005-en-s12, rti-act-2005-en-s1` · rank >10
* **q33** The seller gave me a defective mobile phone and refuses a refund. Can I complain?  
  expected one of `consumer-protection-act-2019-s2, consumer-protection-act-2019-s35, consumer-protection-act-2019-s39` · got `consumer-protection-act-2019-s83, consumer-protection-act-2019-s82, consumer-protection-act-2019-s87` · rank >10
* **m04** प्रथम अपिलासाठी किती फी भरावी लागते?  
  expected one of `mh-rti-rules-2026-07-mr-न5, mh-rti-rules-2026-07-en-r5` · got `rti-rules-2012-central, rti-marathi-s19-s20, rti-fee-rules-2005-r3` · rank >10
* **m07** कोणती माहिती देण्यास नकार देता येतो?  
  expected one of `rti-marathi-exemptions, rti-act-2005-mr-p26, rti-act-2005-en-s8` · got `rti-act-2005-en-s9, rti-act-2005-mr-p28, rti-act-2005-mr-p3` · rank 8
* **m15** सार्वजनिक प्राधिकरणांनी स्वतःहून कोणती माहिती प्रसिद्ध करावी?  
  expected one of `rti-act-2005-mr-p13, rti-act-2005-mr-p14, rti-act-2005-mr-p15, rti-act-2005-en-s4` · got `rti-act-2005-mr-p28, rti-act-2005-mr-p17, rti-act-2005-mr-p67` · rank >10
* **m16** दारिद्र्यरेषेखालील व्यक्तींना माहिती मोफत मिळते का?  
  expected one of `rti-act-2005-mr-p24, rti-act-2005-en-s7` · got `rti-marathi-s6-s7, rti-act-2005-mr-p16, rti-act-2005-mr-p62` · rank >10
