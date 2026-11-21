# Privacy

The data is **pseudonymized**, not anonymous. It is still personal **health** data: "sensitive personal data" under
Mexico's LFPDPPP (the course's reference) and health data under GDPR. So we keep the amount minimal and get consent.
The course also asks: research prototype or medical product? (COFEPRIS). Ours is a research prototype, not a medical device.

## Rules
| What | Where | Allowed |
|---|---|---|
| Name ↔ pseudonym list (`P001` = …) | **paper only**, kept by one person | never digital, never in Git/Azure |
| Subject ID `P001`, operator ID `OP01` | Git, Azure | yes |
| Age bracket (e.g. 20–29), sex, dominant side | consent form / report | only if needed |
| Photos of the **electrodes** (one per session, course requirement) | `figures/` in Git | yes, if no face / tattoo / anything identifying |
| Names, birth date, photos of the person or face, e-mail | — | **never** |
| Raw sEMG + metadata | `data/raw` (private GitHub repo), Azure Storage (EU region) | yes, with consent |

- `make_metadata()` rejects subject/operator IDs that don't match `P###` / `OP##`.
- Free text (`notes`, `placement_notes`): only technical notes, never names or anything identifying.
- Azure: EU region only, Storage Account not public (no anonymous blob access), keys only in `.env` / App settings.
- The GitHub repo stays **private**.
- Deleting data on request: `python scripts/delete_sample.py sample_007` deletes the local folder, the blobs and the
  table rows in one go. Then remove `data/raw/sample_007` from the repo via PR. What it deletes: delete `data/raw/<sample_id>` (via PR), the blob folder `signals/<sample_id>/`,
  and the table rows with `PartitionKey = <sample_id>` / `RowKey = <sample_id>`. Note: the sample stays in the Git
  history; if a full erasure is ever needed, the history has to be rewritten. That's one more reason to keep the repo private.

## Consent form must cover
- Purpose (student project, sEMG contraction detection), what's recorded, voluntary participation, the right to withdraw
- Storage in Microsoft Azure (EU) **and** in a private GitHub repository, until the end of the project
- Contact person
