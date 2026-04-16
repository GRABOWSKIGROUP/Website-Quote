from datetime import date
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Local Contract Builder</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; background:#f7f7f7; }
      .card { max-width: 900px; margin: 0 auto; background: #fff; border:1px solid #ddd; border-radius: 10px; padding: 1rem 1.2rem; }
      .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
      label { font-weight: 600; margin-top: .5rem; display:block; }
      input, textarea { width:100%; padding:.55rem; border:1px solid #ccc; border-radius:8px; }
      textarea { min-height: 120px; }
      .actions { margin-top: 1rem; display:flex; gap:.5rem; }
      button { padding:.65rem .95rem; border-radius:8px; border:none; cursor:pointer; background:#6A282A; color:#fff; }
      .secondary { background:#3b3b3b; }
      pre { white-space: pre-wrap; background:#fafafa; border:1px solid #ddd; border-radius:8px; padding:.9rem; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Local Contract Builder</h1>
      <p>Use this locally to turn an approved quote into a contract draft, then upload/sign in DocuSign.</p>

      <form method="post">
        <div class="grid">
          <div>
            <label>Client Name</label>
            <input name="client_name" value="{{ values.client_name }}" required />
          </div>
          <div>
            <label>Client Email</label>
            <input name="client_email" value="{{ values.client_email }}" required />
          </div>
          <div>
            <label>Project Name</label>
            <input name="project_name" value="{{ values.project_name }}" required />
          </div>
          <div>
            <label>Quote Total (USD)</label>
            <input name="quote_total" value="{{ values.quote_total }}" required />
          </div>
          <div>
            <label>Deposit %</label>
            <input name="deposit_percent" value="{{ values.deposit_percent }}" required />
          </div>
          <div>
            <label>Delivery Timeline (days)</label>
            <input name="delivery_days" value="{{ values.delivery_days }}" required />
          </div>
        </div>

        <label>Scope Summary</label>
        <textarea name="scope_summary" required>{{ values.scope_summary }}</textarea>

        <div class="actions">
          <button type="submit" name="action" value="preview">Preview Contract</button>
          <button class="secondary" type="submit" name="action" value="download">Download .txt for DocuSign</button>
        </div>
      </form>

      {% if contract_text %}
        <h2>Draft Contract</h2>
        <pre>{{ contract_text }}</pre>
      {% endif %}
    </div>
  </body>
</html>
"""


def build_contract(values):
    quote_total = float(values["quote_total"])
    deposit_percent = float(values["deposit_percent"])
    deposit_amount = quote_total * (deposit_percent / 100)
    balance = quote_total - deposit_amount

    return f"""SERVICE AGREEMENT
Date: {date.today().isoformat()}

Provider: JG Tech Solutions
Client: {values['client_name']} ({values['client_email']})
Project: {values['project_name']}

1) Scope of Work
{values['scope_summary']}

2) Project Fee
Total Project Fee: ${quote_total:,.2f}
Deposit ({deposit_percent:.0f}%): ${deposit_amount:,.2f}
Balance Due: ${balance:,.2f}

3) Timeline
Estimated delivery: {values['delivery_days']} calendar days from project kickoff and receipt of required content.

4) Revisions
Includes one reasonable revision pass within original scope.

5) Payment Terms
Deposit due at signing. Final balance due at delivery prior to final transfer/public launch.

6) Signatures
Provider Signature: ________________________   Date: __________
Client Signature:   ________________________   Date: __________

DocuSign Note: Upload this draft into DocuSign and add both parties as signers.
"""


@app.route("/", methods=["GET", "POST"])
def home():
    values = {
        "client_name": "",
        "client_email": "",
        "project_name": "",
        "quote_total": "",
        "deposit_percent": "50",
        "delivery_days": "14",
        "scope_summary": "",
    }
    contract_text = ""

    if request.method == "POST":
        for key in values:
            values[key] = request.form.get(key, "").strip()

        contract_text = build_contract(values)
        if request.form.get("action") == "download":
            filename = f"contract_{values['client_name'].replace(' ', '_') or 'draft'}.txt"
            return Response(
                contract_text,
                mimetype="text/plain",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    return render_template_string(HTML, values=values, contract_text=contract_text)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
