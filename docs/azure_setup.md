# Azure setup (≈ 1 hour, done once by the Azure owner)

## 1. Subscription & resource group
1. Activate **Azure for Students** (https://azure.microsoft.com/free/students, no credit card needed).
2. Portal → Resource groups → Create: `rg-semgia`, region **West Europe**.
   Azure for Students only allows a few regions for resources (policy "Allowed resource deployment regions":
   chilecentral, westus2, belgiumcentral, canadacentral, brazilsouth). The only EU one is **belgiumcentral** → use it
   for the Storage Account and the App Service (privacy: EU only). Our account: `semgiadatabossvl`.
3. Resource group → Access control (IAM) → add the other 3 members as **Contributor**.
4. Cost Management → Budgets → create a budget for `rg-semgia`: €10, with an e-mail alert at 80%.

## 2. Storage Account (data)
1. Create → Storage account: name e.g. `semgiadata<random>`, region the same as above, Performance **Standard**,
   Redundancy **LRS**.
2. Advanced: **Allow blob anonymous access = disabled**. Leave the rest as the defaults.
3. After it's created: Security + networking → **Access keys** → copy the *Connection string*.
4. Every team member: `cp .env.example .env` and paste it after `AZURE_STORAGE_CONNECTION_STRING=`.
   Share it privately (e.g. in a direct message, then delete the message), **never in Git**.
5. You don't need to create the container/tables: the first recording creates `signals`, `samples` and `predictions`.

Test: `python scripts/record.py --source mock` → Collect sample → Storage browser should show `signals/sample_NNN/...`.

## 3. App Service (dashboard)
Requires the Azure CLI (`az login --use-device-code`). `az webapp up` no longer works (deprecated), so it is 4 steps.
We use the **free F1** plan (no cost; slow, sleeps when idle → the first load can take ~1 min).
```
az appservice plan create -n semgia-plan -g rg-semgia --sku F1 --is-linux -l belgiumcentral
az webapp create -n semgia-dashboard-bossvl -g rg-semgia -p semgia-plan --runtime "PYTHON:3.12"
az webapp config set -n semgia-dashboard-bossvl -g rg-semgia --web-sockets-enabled true \
    --startup-file "python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0"
az webapp config appsettings set -n semgia-dashboard-bossvl -g rg-semgia \
    --settings AZURE_STORAGE_CONNECTION_STRING="<connection string>" SCM_DO_BUILD_DURING_DEPLOYMENT=true
cd dashboard && zip dashboard.zip app.py requirements.txt
az webapp deploy -n semgia-dashboard-bossvl -g rg-semgia --src-path dashboard.zip --type zip
```
Open **https://semgia-dashboard-bossvl.azurewebsites.net**. To redeploy after changes: repeat the last two lines
(don't commit `dashboard.zip`).

## 4. Done – checklist
- [ ] all 4 have Contributor access
- [ ] budget alert set
- [ ] every member has a working `.env`
- [ ] the mock recording appears in the dashboard
- [ ] after the project: delete `rg-semgia` (this deletes everything)
