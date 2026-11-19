# Azure setup (≈ 1 hour, done once by the Azure owner)

## 1. Subscription & resource group
1. Activate **Azure for Students** (https://azure.microsoft.com/free/students, no credit card needed).
2. Portal → Resource groups → Create: `rg-semgia`, region **West Europe** (or Germany West Central).
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
Requires the Azure CLI (`az login`):
```
cd dashboard
az webapp up --name semgia-dashboard-<random> --resource-group rg-semgia \
    --runtime PYTHON:3.12 --sku B1 --location westeurope
az webapp config set --name semgia-dashboard-<random> --resource-group rg-semgia --web-sockets-enabled true \
    --startup-file "python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0"
az webapp config appsettings set --name semgia-dashboard-<random> --resource-group rg-semgia \
    --settings AZURE_STORAGE_CONNECTION_STRING="<connection string>" SCM_DO_BUILD_DURING_DEPLOYMENT=true
```
Open `https://semgia-dashboard-<random>.azurewebsites.net`.
To redeploy after changes, run `az webapp up` again from `dashboard/` (it remembers the settings).
- B1 costs ~€12/month and is covered by the student credit. Stop the app when not needed
  (`az webapp stop ...`). F1 (free) may work too, but it sleeps and is slow.
- Optional: put the dashboard behind a login (App Service → Authentication → Microsoft).

## 4. Done – checklist
- [ ] all 4 have Contributor access
- [ ] budget alert set
- [ ] every member has a working `.env`
- [ ] the mock recording appears in the dashboard
- [ ] after the project: delete `rg-semgia` (this deletes everything)
