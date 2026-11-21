# dashboard/ – Streamlit dashboard (runs on Azure App Service)

`app.py` shows: the sample list, metadata (placement, effort, condition), the 24 s raw signal, the timer label line
next to the AI output (0/1 per 100 ms window) with AI contraction % + agreement %, and a table of contraction % and
agreement % per sample. `STEPS` is a copy of `config.SAMPLE_STEPS` (self-contained): change both together.

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
Live (free F1 plan, first load ~1 min): https://semgia-dashboard-bossvl.azurewebsites.net
`az webapp up` is deprecated → redeploy = zip `app.py` + `requirements.txt` and `az webapp deploy` (exact commands in the guide).
No paid plans (team choice).
Startup command: `python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0`
App setting: `AZURE_STORAGE_CONNECTION_STRING`. Turn on Web sockets.
