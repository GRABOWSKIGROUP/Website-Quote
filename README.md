# Flask Quote Generator

A simple Flask application to generate website project quotes using tiered pricing.

## Pricing rules

- Flat static: $750 base
- Mid tier: $1,200 base
- Detailed/full featured: $2,500 base
- Forms: $150 each
- E-commerce: $800
- Backend/admin panel: $500
- Third party integrations: $200 each
- Military/First Responder discount: 20% off total
- Rush 48hr: 15% added to total

## Output options

- Text summary
- PDF download
- Email quote (SMTP must be configured)

## Run locally

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Start the app:

```bash
python app.py
```

3. Open `http://127.0.0.1:5000` in your browser.

## Make it accessible anytime

### Option 1: Use it yourself on your own computer

- Keep the project on your machine and run it whenever needed with `python app.py`
- If you want to access it from other devices on your local network, start it with:

```bash
set FLASK_HOST=0.0.0.0
python app.py
```

- Then open `http://YOUR-COMPUTER-IP:5000` from another device on the same Wi-Fi/network

### Option 2: Share it with potential clients online

The easiest path is to deploy it to a small Python host such as Render, Railway, or PythonAnywhere.

Recommended setup:

1. Push this project to GitHub
2. Create a new Web Service on Render
3. Use these settings:
	- Build command: `pip install -r requirements.txt`
	- Start command: `gunicorn wsgi:app`
4. Add environment variables:
	- `SECRET_KEY`
	- `SEND_EMAIL`
	- `SMTP_SERVER`
	- `SMTP_PORT`
	- `SMTP_USERNAME`
	- `SMTP_PASSWORD`
	- `SMTP_FROM_EMAIL`
5. Render will give you a public URL you can send to clients anytime

## Deployment files included

- `render.yaml` — one-click style setup for Render
- `Procfile` — process definition for platforms that expect it
- `.env.example` — copy of required environment variables for local or hosted configuration
- `wsgi.py` — production entrypoint used by `gunicorn`

## Deploy to Render

1. Create a GitHub repository and push this project
2. Log in to Render and choose **New +** → **Blueprint** or **Web Service**
3. Connect your GitHub repository
4. If using the included `render.yaml`, Render can read the settings automatically
5. If setting it up manually, use:

```bash
Build command: pip install -r requirements.txt
Start command: gunicorn wsgi:app
```

6. Add or confirm these environment variables in Render:
	- `SECRET_KEY`
	- `FLASK_DEBUG=false`
	- `SEND_EMAIL=false` by default unless email is configured
	- `SMTP_SERVER`
	- `SMTP_PORT`
	- `SMTP_USERNAME`
	- `SMTP_PASSWORD`
	- `SMTP_FROM_EMAIL`
7. Deploy the service
8. Render will provide a public URL like `https://your-app.onrender.com`

## Deploy to Railway

1. Push the project to GitHub
2. Create a new Railway project from the GitHub repo
3. Add the same environment variables listed above
4. Railway should detect Python automatically
5. Use `gunicorn wsgi:app` as the start command if needed

## Deploy to Vercel

If you want the flow to be GitHub → Vercel → shareable link, this project is now set up for that too.

Files used for Vercel:

- `api/index.py` — Vercel Python entrypoint that imports the Flask app
- `vercel.json` — routes all requests to the Flask app

Steps:

1. Push this project to GitHub
2. Log in to Vercel
3. Choose **Add New Project** and import the GitHub repository
4. Vercel should detect the included `vercel.json`
5. Add environment variables in the Vercel dashboard if needed:
	- `SECRET_KEY`
	- `SEND_EMAIL`
	- `SMTP_SERVER`
	- `SMTP_PORT`
	- `SMTP_USERNAME`
	- `SMTP_PASSWORD`
	- `SMTP_FROM_EMAIL`
6. Click deploy
7. Vercel will provide a public URL you can send to clients

### Vercel note

Vercel runs Python apps as serverless functions. That is usually fine for a lightweight quote form like this, but if you later add larger file handling, long-running admin actions, or more advanced backend behavior, Render or Railway may be a better long-term fit.

## Local environment file

To use a local env file for your own machine, copy `.env.example` to `.env` and set real values.

This is the easiest option on Windows because you do not need to type environment variables into PowerShell every time.

Example `.env` file:

```env
SECRET_KEY=replace-with-a-secure-key
SEND_EMAIL=true
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587
SMTP_USERNAME=you@yourdomain.com
SMTP_PASSWORD=your-zoho-password-or-app-password
SMTP_FROM_EMAIL=quotes@yourdomain.com
```

Then just run:

```powershell
python app.py
```

Example PowerShell startup with a local-only configuration:

```powershell
$env:SECRET_KEY="replace-with-a-secure-key"
$env:FLASK_DEBUG="true"
$env:SEND_EMAIL="false"
python app.py
```

Important: in PowerShell, `SEND_EMAIL="true"` is not valid syntax. Use `$env:SEND_EMAIL="true"` instead.

### Best option for your use case

- If only you need it occasionally: run it locally
- If you want clients to fill it out themselves: deploy it on Render or Railway
- If you want a custom branded link later: connect your own domain after deployment

## Configure email

Set these environment variables on your machine or hosting provider:

- `SEND_EMAIL=true`
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`

Example for local PowerShell:

```powershell
$env:SEND_EMAIL="true"
$env:SMTP_SERVER="smtp.yourprovider.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="you@example.com"
$env:SMTP_PASSWORD="your-password"
$env:SMTP_FROM_EMAIL="quotes@yourdomain.com"
python app.py
```

### Zoho Mail setup

If you have a Zoho account, use these SMTP settings:

- `SMTP_SERVER=smtp.zoho.com`
- `SMTP_PORT=587`
- `SMTP_USERNAME=you@yourdomain.com`
- `SMTP_FROM_EMAIL=quotes@yourdomain.com`
- `SEND_EMAIL=true`

For the password:

- Use your Zoho mailbox password if SMTP access is enabled
- If your Zoho account uses MFA, create and use an app-specific password instead

Example PowerShell setup for Zoho:

```powershell
$env:SEND_EMAIL="true"
$env:SMTP_SERVER="smtp.zoho.com"
$env:SMTP_PORT="587"
$env:SMTP_USERNAME="you@yourdomain.com"
$env:SMTP_PASSWORD="your-zoho-password-or-app-password"
$env:SMTP_FROM_EMAIL="quotes@yourdomain.com"
python app.py
```

If you deploy to Vercel, add the same values in the Vercel project environment variables page.

## Bot protection (Cloudflare Turnstile)

The quote form supports optional bot protection using Cloudflare Turnstile.

1. Create a Turnstile widget in Cloudflare
2. Add these environment variables locally and in Vercel:
	- `TURNSTILE_SITE_KEY`
	- `TURNSTILE_SECRET_KEY`
3. Redeploy (or restart locally)

Behavior:

- If both keys exist, verification is required on quote submission
- If keys are missing, bot protection is automatically disabled

## Local contract app (for DocuSign handoff)

A separate local-only app is included to turn approved quote details into a contract draft text file.

File:

- `local_contract_app.py`

Run locally:

```bash
python local_contract_app.py
```

Then open:

```text
http://127.0.0.1:5050
```

Use the form to preview/download a contract `.txt`, then upload that file into DocuSign and assign both parties as signers.
