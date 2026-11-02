# Extolla Cost-to-Serve Modeller

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Starts with a **blank model**. Use **Load fictional example** to see fabricated customers and illustrative costs. This example does not contain Brisbane Logistics customer identities, private rate schedules or actual P&L amounts.

The app has editable business assumptions, P&L allocation, rate-card services, annual activity volumes, customer-specific rates, customer profitability, pricing opportunities, scenario uplift, proposed customer modelling and Excel/JSON exports.

## Deployment

Set `DATABASE_URL` to a persistent PostgreSQL URL for hosted production environments (e.g. `postgresql+psycopg2://...`). Local default is SQLite; SQLite on Streamlit Community Cloud may be lost during restart/redeploy. Configure connection credentials securely via environment variables; do not commit secrets. `app.py` and `requirements.txt` are at the repository root.

**Security:** This prototype has no login/authentication. Do not deploy publicly with sensitive client financials. Add authentication, warehouse-level access control and a private database before any production use.

## Important fidelity limitations

- The workbook contains externally linked XLOOKUP volume formulas, which cannot be automatically reproduced from the provided standalone file.
- This initial application is an operational prototype, **not an independently reconciled replication of every Excel formula**.
- Storage cost is allocated from capacity-equivalent pallet-weeks. Activity bottom-up labour/MHE is shown alongside its P&L pool reconciliation gap; the P&L activity pool is not double-charged to customers.
- Customer overhead uses 20% equal / 80% transaction activity; this uses service-unit counts as a proxy. Validate the workbook's exact transaction-driver definition before relying on results.
- Prospective customer view is fully loaded only; incremental cost treatment requires extra assumptions around step-fixed capacity and equipment requirements.
- Full legacy workbook import, PDF reporting and detailed multi-variable scenarios are subsequent development items.
