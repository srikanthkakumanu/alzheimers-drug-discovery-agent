# Glossary

Shared definitions so records and prompts can link here instead of re-explaining terms.

## Decision model
| Term | Meaning |
| --- | --- |
| Rating | 0–5 judgment per dimension (efficacy, safety, BBB, manufacturing); higher is better; `null` = unknown |
| Weighted score | Σ weight × rating / 5 on a 0–100 scale; `null` if any rating is `null`. Illustrative, not a success probability |
| Provisional score | Score built on incomplete or preliminary evidence; all current scores are provisional |
| `score_history` | Earlier score kept for audit after its evidence was disputed; never used for ranking |
| `rating_evidence` | Experiment IDs that justify each rating |
| Gate | Independent pass / fail / unknown check: `identity`, `orthogonal_activity`, `replication`, `cns_exposure_engagement`, `safety`, `manufacturing` |
| Hard block | Confirmed artifact, safety signal, or replication failure; forces disposition `blocked` |
| Disposition | `follow-up` (gather more evidence) · `hold` (specific gap) · `blocked` (hard block or failed gate) · `provisional` (no valid ratings) · `deprioritized` (weak case) · `promoted` (not permitted in this demonstration) |
| Human disposition | A decision recorded by an accountable person; a model or role cannot create one |
| Decision packet | Role output for the human owner: comparison, gates, uncertainty, recommended next action |
| Campaign period | Fictional relative step (01–12) in the synthetic scenario, not a date |

## Scientific terms
| Term | Meaning |
| --- | --- |
| Orthogonal assay | Readout using a different detection principle, to rule out artifacts |
| Technical repeat / independent preparation / independent site | Wells in one run / separately prepared biological material / a different lab; only the latter two support replication |
| IC50 / CC50 | Concentration giving half-maximal inhibition / half-maximal cytotoxicity |
| hERG | Cardiac ion channel; inhibition is an early arrhythmia-risk screen |
| Papp / efflux ratio | In vitro apparent permeability / transporter-driven efflux; not brain exposure |
| Kp,uu | Unbound brain-to-plasma ratio; requires in vivo measurement |
| Z-prime | Assay-quality statistic; < 0.5 is commonly treated as inadequate separation |
| PAINS | Substructures that frequently cause assay interference |
| ASO | Antisense oligonucleotide (a Tau-lowering modality distinct from small molecules) |
| Target engagement | Evidence the drug acts on its target; not clinical benefit |
| CDR-SB | Clinical Dementia Rating–Sum of Boxes, a common clinical endpoint |
| CMC | Chemistry, manufacturing, and controls evidence for a drug substance |
| IND | Investigational New Drug application (US) |
