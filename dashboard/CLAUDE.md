# dashboard/ – Streamlit dashboard (runs on Azure App Service)

`app.py` shows: the sample list, metadata (placement, effort, condition), the 24 s raw signal and the share of time in
contraction per 2 s chunk.

## Rules
- **Read-only.** The dashboard never writes to Azure.
- **Self-contained:** it does NOT import `semgia` (App Service only deploys this folder). Its own deps are in
  `dashboard/requirements.txt`.
- Data source: Azure Storage if `AZURE_STORAGE_CONNECTION_STRING` is set, otherwise local `../data/raw` (dev mode).
  Keep both paths working.
- Azure layout it reads (written by `semgia/storage.py`, keep them in sync):
  blob `signals/<sample_id>/<seq:06d>.csv` (one int per line, 2 s each), table `samples`
  (PartitionKey="sample"), table `predictions` (PartitionKey=sample_id, fields t0_s, n, contract_ratio, labels).
- Plain Streamlit charts only (`st.line_chart`, `st.bar_chart`, `st.metric`). No extra plotting libraries.
- Never display anything other than pseudonyms.

## Run locally
`streamlit run dashboard/app.py` → http://localhost:8501

## Deploy (details in docs/azure_setup.md)
From inside `dashboard/`: `az webapp up --name semgia-dashboard --runtime PYTHON:3.12 --sku B1 --location westeurope`
Startup command: `python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0`
App setting: `AZURE_STORAGE_CONNECTION_STRING`. Turn on Web sockets.
