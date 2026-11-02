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

## Interface update (November 2026)
- Horizontal page navigation and Extolla top colour bar; no navigation sidebar.
- Editable Business Inputs divided into General Business, Positions Available and Space Utilisation. IBC defaults to 1.20 pallet equivalents; existing saved models retain their own assumptions.
- All-customer volume and rate matrices automatically follow active services in the rate card.
- Customer-level profitability charts and two-decimal, centrally aligned output tables.
- The optional AI pricing review requires an `OPENAI_API_KEY` in the app's Streamlit Cloud **Settings > Secrets**. Do not put API keys in GitHub. The AI button sends the pricing service summary to the OpenAI API; only use it with approved data. Without a key, the button shows a configuration warning.
- Saved models created before this update may contain old warehouse-space factors; review and update assumptions after loading them.
- This remains a prototype: no complete workbook reconciliation, private authentication, or persistent-cloud database has been established. Do not upload confidential client data to a public deployment.
