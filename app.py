import os
import smtplib
import urllib.parse
import urllib.request
import json
from email.message import EmailMessage
from email.utils import formataddr
from io import BytesIO

from flask import Flask, flash, render_template, request, send_file
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "replace-with-secure-secret")

PRICES = {
    "tiers": {
        "flat": 750,
        "mid": 1200,
        "detailed": 2500,
    },
    "forms": 150,
    "ecommerce": 800,
    "backend": 500,
    "integrations": 200,
}

SMTP_CONFIG = {
    "server": os.getenv("SMTP_SERVER", "smtp.example.com"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("SMTP_USERNAME", "user@example.com"),
    "password": os.getenv("SMTP_PASSWORD", "password"),
    "from_email": os.getenv("SMTP_FROM_EMAIL", "quotes@example.com"),
    "from_name": os.getenv("SMTP_FROM_NAME", "JG Tech Solutions"),
}

SEND_EMAIL = os.getenv("SEND_EMAIL", "false").lower() == "true"
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "")
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")
BOT_PROTECTION_ENABLED = bool(TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY)


@app.context_processor
def inject_template_config():
    return {
        "bot_protection_enabled": BOT_PROTECTION_ENABLED,
        "turnstile_site_key": TURNSTILE_SITE_KEY,
    }


def verify_turnstile(token, remote_ip=None):
    if not BOT_PROTECTION_ENABLED:
        return True, "disabled"

    if not token:
        return False, "missing-token"

    payload = {
        "secret": TURNSTILE_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            parsed = json.loads(body.decode("utf-8"))
            success = bool(parsed.get("success"))
            errors = parsed.get("error-codes", [])
            return success, ",".join(errors) if errors else "ok"
    except Exception as exc:
        return False, str(exc)


def calculate_quote(data):
    tier = data.get("tier", "flat")
    forms = int(data.get("forms", 0))
    ecommerce = data.get("ecommerce") == "yes"
    backend = data.get("backend") == "yes"
    integrations = int(data.get("integrations", 0))
    discount = data.get("military") == "yes"
    rush = data.get("rush") == "yes"

    items = [
        {"label": "Base price", "amount": PRICES["tiers"][tier]},
        {"label": "Forms", "amount": forms * PRICES["forms"], "quantity": forms},
    ]

    if ecommerce:
        items.append({"label": "E-commerce", "amount": PRICES["ecommerce"]})
    if backend:
        items.append({"label": "Backend / Admin Panel", "amount": PRICES["backend"]})
    if integrations:
        items.append({"label": "Third-party integrations", "amount": integrations * PRICES["integrations"], "quantity": integrations})

    subtotal = sum(item["amount"] for item in items)
    discount_amount = subtotal * 0.20 if discount else 0
    after_discount = subtotal - discount_amount
    rush_amount = after_discount * 0.15 if rush else 0
    total = after_discount + rush_amount

    return {
        "client_name": data.get("client_name", ""),
        "project_name": data.get("project_name", "Website Quote"),
        "tier": tier,
        "items": items,
        "subtotal": subtotal,
        "discount": discount_amount,
        "rush": rush_amount,
        "total": total,
        "discount_applied": discount,
        "rush_applied": rush,
        "output_type": data.get("output", "text"),
        "email": data.get("email", ""),
    }


def create_pdf(quote):
    bg = colors.HexColor("#F5F5F5")
    surface = colors.HexColor("#FFFFFF")
    line = colors.HexColor("#D8D4D4")
    brand_dark = colors.HexColor("#101010")
    brand = colors.HexColor("#6A282A")
    brand_soft = colors.HexColor("#85384D")
    text_dark = colors.HexColor("#101010")
    text_muted = colors.HexColor("#626161")
    panel_bg = colors.HexColor("#FBFBFB")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Project Quote")

    page_width, page_height = letter
    margin = 34
    card_x = margin
    card_y = 30
    card_w = page_width - (margin * 2)
    card_h = page_height - (margin + card_y)

    # Page and card surfaces to match site chrome.
    pdf.setFillColor(bg)
    pdf.rect(0, 0, page_width, page_height, stroke=0, fill=1)

    pdf.setFillColor(colors.HexColor("#E7E3E3"))
    pdf.roundRect(card_x + 3, card_y - 3, card_w, card_h, 14, stroke=0, fill=1)

    pdf.setFillColor(surface)
    pdf.setStrokeColor(line)
    pdf.roundRect(card_x, card_y, card_w, card_h, 14, stroke=1, fill=1)

    # Header gradient close to web UI (155deg approximation).
    header_height = 108
    header_y = card_y + card_h - header_height

    gradient_steps = 160
    start = (16, 16, 16)
    mid = (58, 26, 29)
    end = (133, 56, 77)
    for i in range(gradient_steps):
        t = i / (gradient_steps - 1)
        if t < 0.44:
            local_t = t / 0.44
            r = int(start[0] + (mid[0] - start[0]) * local_t)
            g = int(start[1] + (mid[1] - start[1]) * local_t)
            b = int(start[2] + (mid[2] - start[2]) * local_t)
        else:
            local_t = (t - 0.44) / 0.56
            r = int(mid[0] + (end[0] - mid[0]) * local_t)
            g = int(mid[1] + (end[1] - mid[1]) * local_t)
            b = int(mid[2] + (end[2] - mid[2]) * local_t)
        pdf.setFillColor(colors.Color(r / 255, g / 255, b / 255))
        x = card_x + (card_w * i / gradient_steps)
        pdf.rect(x, header_y, (card_w / gradient_steps) + 1, header_height, stroke=0, fill=1)

    # Optional logo in header (same branding asset used in web UI).
    logo_path = os.path.join(os.path.dirname(__file__), "static", "lOGO.png")
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            pdf.drawImage(
                logo,
                card_x + card_w - 228,
                header_y - 2,
                width=182,
                height=96,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawString(card_x + 22, header_y + 66, "Project Quote")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(card_x + 22, header_y + 47, "Branded estimate with itemized pricing")

    # Quote identity panel.
    panel_top = header_y - 16
    panel_height = 76
    pdf.setFillColor(panel_bg)
    pdf.setStrokeColor(line)
    pdf.roundRect(card_x + 18, panel_top - panel_height, card_w - 36, panel_height, 8, stroke=1, fill=1)

    pdf.setFillColor(text_dark)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(card_x + 30, panel_top - 22, f"Client: {quote['client_name'] or 'N/A'}")
    pdf.drawString(card_x + 30, panel_top - 40, f"Project: {quote['project_name']}")
    pdf.drawString(card_x + 30, panel_top - 58, f"Package Tier: {quote['tier'].capitalize()}")

    # Itemized pricing table.
    table_top = panel_top - panel_height - 24
    table_x = card_x + 18
    table_width = card_w - 36
    row_height = 22

    pdf.setFillColor(brand_dark)
    pdf.roundRect(table_x, table_top - row_height, table_width, row_height, 6, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(table_x + 10, table_top - 15, "Description")
    pdf.drawRightString(table_x + table_width - 10, table_top - 15, "Amount")

    y = table_top - row_height
    pdf.setFont("Helvetica", 10)
    toggle = False

    for item in quote["items"]:
        label = item["label"]
        amount = item["amount"]
        quantity = item.get("quantity")
        if quantity is not None:
            label = f"{label} (x{quantity})"

        toggle = not toggle
        if toggle:
            pdf.setFillColor(colors.HexColor("#F8F6F6"))
            pdf.rect(table_x, y - row_height, table_width, row_height, stroke=0, fill=1)

        pdf.setFillColor(text_dark)
        pdf.drawString(table_x + 10, y - 15, label)
        pdf.drawRightString(table_x + table_width - 10, y - 15, f"${amount:,.2f}")
        y -= row_height

    if quote["discount_applied"]:
        pdf.setFillColor(colors.HexColor("#F8F6F6"))
        pdf.rect(table_x, y - row_height, table_width, row_height, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#8A1E1E"))
        pdf.drawString(table_x + 10, y - 15, "Military / First Responder Discount (20%)")
        pdf.drawRightString(table_x + table_width - 10, y - 15, f"-${quote['discount']:,.2f}")
        y -= row_height

    if quote["rush_applied"]:
        pdf.setFillColor(text_dark)
        pdf.drawString(table_x + 10, y - 15, "Rush 48hr surcharge (15%)")
        pdf.drawRightString(table_x + table_width - 10, y - 15, f"${quote['rush']:,.2f}")
        y -= row_height

    # Total row
    pdf.setFillColor(brand)
    pdf.roundRect(table_x, y - row_height - 2, table_width, row_height + 2, 6, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(table_x + 10, y - 16, "Total")
    pdf.drawRightString(table_x + table_width - 10, y - 16, f"${quote['total']:,.2f}")

    pdf.setFillColor(text_muted)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(card_x + 18, 32, "Generated by JG Tech Solutions Quote Generator")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


def build_quote_email_message(recipient, quote, pdf_bytes):
    message = EmailMessage()
    message["Subject"] = f"Your quote for {quote['project_name']}"
    message["From"] = formataddr((SMTP_CONFIG["from_name"], SMTP_CONFIG["from_email"]))
    message["To"] = recipient

    lines = [
        f"Hello {quote['client_name'] or 'there'},",
        "",
        f"Attached is your quote for {quote['project_name']}.",
        "A summary is included below for quick reference.",
        "",
        f"Client: {quote['client_name']}",
        f"Project: {quote['project_name']}",
        "",
        "Line items:",
    ]
    for item in quote["items"]:
        label = item["label"]
        quantity = item.get("quantity")
        amount = item["amount"]
        if quantity is not None:
            lines.append(f"- {label} x{quantity}: ${amount:,.2f}")
        else:
            lines.append(f"- {label}: ${amount:,.2f}")

    lines.append("")
    if quote["discount_applied"]:
        lines.append(f"Military / First Responder Discount: -${quote['discount']:,.2f}")
    if quote["rush_applied"]:
        lines.append(f"Rush 48hr surcharge: +${quote['rush']:,.2f}")
    lines.append(f"Total: ${quote['total']:,.2f}")
    lines.extend([
        "",
        "Thank you,",
        "Quote Generator",
    ])
    message.set_content("\n".join(lines))
    message.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename="quote.pdf",
    )
    return message


def send_quote_email(recipient, quote):
    if not SEND_EMAIL:
        raise RuntimeError("Email sending is disabled. Set SEND_EMAIL = True and configure SMTP_CONFIG.")

    pdf_buffer = create_pdf(quote)
    message = build_quote_email_message(recipient, quote, pdf_buffer.getvalue())

    with smtplib.SMTP(SMTP_CONFIG["server"], SMTP_CONFIG["port"]) as smtp:
        smtp.starttls()
        smtp.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
        smtp.send_message(message)


@app.route("/", methods=["GET"])
def index():
    return render_template("form.html")


@app.route("/quote", methods=["GET", "POST"])
def quote():
    if request.method == "GET":
        return render_template("form.html")

    if BOT_PROTECTION_ENABLED:
        token = request.form.get("cf-turnstile-response", "")
        remote_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        ok, _reason = verify_turnstile(token, remote_ip)
        if not ok:
            flash("Verification failed. Please confirm you are human and submit again.", "danger")
            return render_template("form.html"), 400

    quote = calculate_quote(request.form)
    output_type = quote["output_type"]

    if output_type == "pdf":
        pdf_buffer = create_pdf(quote)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="quote.pdf",
            mimetype="application/pdf",
        )

    if output_type == "email":
        if not quote["email"]:
            return render_template(
                "email_status.html",
                quote=quote,
                status="error",
                title="Email address required",
                message="Enter a valid recipient email address to send the quote PDF.",
                details="Add the client's email address and submit again.",
            ), 400
        try:
            send_quote_email(quote["email"], quote)
            return render_template(
                "email_status.html",
                quote=quote,
                status="success",
                title="Quote sent successfully",
                message=f"The quote and PDF attachment were sent to {quote['email']}.",
                details="Ask the client to check their inbox and spam folder if they do not see it right away.",
            )
        except Exception as exc:
            return render_template(
                "email_status.html",
                quote=quote,
                status="error",
                title="Email could not be sent",
                message="The quote was generated, but the email delivery failed.",
                details=str(exc),
            ), 502

    return render_template("quote.html", quote=quote)


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
