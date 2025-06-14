from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from email.message import EmailMessage
from email.utils import formataddr
from jinja2 import Template
import smtplib
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Přihlašovací údaje
DB_HOST = "db"         # název služby z docker-compose
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "postgres"

try:
    # Připojení k databázi
    conn = psycopg2.connect(
        host=DB_HOST,
        port=5432,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()
    print("✅ Připojení k databázi bylo úspěšné.")

except Exception as e:
    print("❌ Chyba při připojování k databázi:", e)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    results = cur.execute("SELECT * FROM zajemci")
    print(results)

    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/submit")
async def submit_form(name: str = Form(...), email: str = Form(...)):
    try:
        # ⬇️ Cesta k existujícímu PDF souboru
        pdf_path = "static/Startujeme předškoláky - informace.pdf"  # uprav dle tvé struktury

        # ⬇️ Vytvoření e-mailu
        msg = EmailMessage()
        msg['Subject'] = 'Startujeme předškoláky - Jak na to?'
        msg['From'] = formataddr(("STARTUJEME PŘEDŠKOLÁKY", "info@startujemepredskolaky.cz"))
        msg['To'] = email

        with open("templates/email_template.html", "r", encoding="utf-8") as f:
            html_template = Template(f.read())
        html_body = html_template.render(name=name)

        msg.set_content("E-mail s HTML verzí.")  # fallback pro starší klienty
        msg.add_alternative(html_body, subtype='html')

        # ⬇️ Příloha PDF
        with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename="Startujeme předškoláky - informace.pdf"
            )

        with smtplib.SMTP("smtp.forpsi.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login("info@startujemepredskolaky.cz", os.getenv("mail_password"))
            smtp.send_message(msg)

        cur.execute("INSERT INTO zajemci (name, email) VALUES (%s, %s)", (name, email))
        conn.commit()

        # ⬇️ Vytvoření e-mailu
        msg2 = EmailMessage()
        msg2['Subject'] = 'Startujeme předškoláky - Jak na to?'
        msg2['From'] = formataddr(("STARTUJEME PŘEDŠKOLÁKY", "info@startujemepredskolaky.cz"))
        msg2['To'] = "info@startujemepredskolaky.cz"
        msg2.set_content(f"Zaslán e-mail pro {name} na adresu {email}.")

        with smtplib.SMTP("smtp.forpsi.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login("info@startujemepredskolaky.cz", os.getenv("mail_password"))
            smtp.send_message(msg2)

        return RedirectResponse(url="/", status_code=303)
    
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
