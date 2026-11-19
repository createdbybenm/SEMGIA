# Privacy

The data is **pseudonymized**, not anonymous. Under GDPR it is still personal (health) data,
so we keep the amount minimal and get consent.

## Rules
| What | Where | Allowed |
|---|---|---|
| Name ↔ pseudonym list (`P001` = …) | **paper only**, kept by one person | never digital, never in Git/Azure |
| Subject ID `P001`, operator ID `OP01` | Git, Azure | yes |
| Age bracket (e.g. 20–29), sex, dominant side | consent form / report | only if needed |
| Names, birth date, photos of the person, e-mail | — | **never** |
| Raw sEMG + metadata | `data/raw` (private GitHub repo), Azure Storage (EU region) | yes, with consent |

- `make_metadata()` rejects subject/operator IDs that don't match `P###` / `OP##`.
- Free text (`notes`, `placement_notes`): only technical notes, never names or anything identifying.
- Azure: EU region only, Storage Account not public (no anonymous blob access), keys only in `.env` / App settings.
- The GitHub repo stays **private**.
- Deleting data on request: delete `data/raw/<sample_id>` (via PR), the blob folder `signals/<sample_id>/`,
  and the table rows with `PartitionKey = <sample_id>` / `RowKey = <sample_id>`. Note: the sample stays in the Git
  history; if a full erasure is ever needed, the history has to be rewritten. That's one more reason to keep the repo private.

## Consent form must cover
- Purpose (student project, sEMG contraction detection), what's recorded, voluntary participation, the right to withdraw
- Storage in Microsoft Azure (EU) **and** in a private GitHub repository, until the end of the project
- Contact person
