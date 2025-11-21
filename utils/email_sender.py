"""
Modulo per l'invio di email e notifiche
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st
from datetime import datetime


def send_monthly_report(recipient_email, report_data, attachment_path=None):
    """
    Invia report mensile via email

    Args:
        recipient_email: Email destinatario
        report_data: Dict con dati del report
        attachment_path: Path opzionale per allegato

    Returns:
        True se invio riuscito, False altrimenti
    """
    try:
        # Leggi credenziali da secrets
        if 'email' not in st.secrets:
            st.error("⚠️ Configurazione email mancante. Vedi documentazione per configurare Gmail.")
            return False

        sender_email = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]

        # Crea messaggio
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = f"📊 Report Spese Familiari - {report_data.get('month', 'N/A')}"

        # Corpo email
        body = create_email_body(report_data)

        message.attach(MIMEText(body, "html"))

        # Aggiungi allegato se presente
        if attachment_path:
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                filename = attachment_path.split('/')[-1]
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )
                message.attach(part)
            except Exception as e:
                st.warning(f"Impossibile allegare file: {e}")

        # Invia email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(message)

        return True

    except Exception as e:
        st.error(f"❌ Errore nell'invio email: {str(e)}")
        return False


def create_email_body(report_data):
    """Crea corpo HTML dell'email"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .metric {{
                background: white;
                padding: 20px;
                margin: 15px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .metric-title {{
                color: #666;
                font-size: 14px;
                margin-bottom: 5px;
            }}
            .metric-value {{
                color: #333;
                font-size: 28px;
                font-weight: bold;
            }}
            .category-item {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }}
            .alert {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
            .alert-critical {{
                background: #f8d7da;
                border-left: 4px solid #dc3545;
            }}
            .footer {{
                text-align: center;
                color: #666;
                font-size: 12px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>💰 Report Spese Familiari</h1>
            <p>{report_data.get('month', 'N/A')}</p>
        </div>

        <div class="content">
            <div class="metric">
                <div class="metric-title">Spesa Totale del Mese</div>
                <div class="metric-value">€{report_data.get('total', 0):,.2f}</div>
            </div>

            <div class="metric">
                <div class="metric-title">Numero di Transazioni</div>
                <div class="metric-value">{report_data.get('transaction_count', 0)}</div>
            </div>

            <div class="metric">
                <div class="metric-title">Spesa Media Giornaliera</div>
                <div class="metric-value">€{report_data.get('daily_average', 0):,.2f}</div>
            </div>

            <h3 style="margin-top: 30px;">📊 Top Categorie</h3>
            <div style="background: white; padding: 20px; border-radius: 8px;">
                {report_data.get('top_categories_html', '<p>Nessun dato disponibile</p>')}
            </div>

            {create_alerts_html(report_data.get('alerts', []))}

            <h3 style="margin-top: 30px;">💡 Consigli</h3>
            <div style="background: white; padding: 20px; border-radius: 8px;">
                {report_data.get('recommendations', '<p>Continua così!</p>')}
            </div>
        </div>

        <div class="footer">
            <p>📱 Generato da Family Expense Tracker</p>
            <p>{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
    </body>
    </html>
    """

    return html


def create_alerts_html(alerts):
    """Crea HTML per gli alert"""
    if not alerts:
        return ""

    html = '<h3 style="margin-top: 30px;">⚠️ Alert Budget</h3>'

    for alert in alerts:
        alert_class = "alert-critical" if alert.get('severity') in ['exceeded', 'critical'] else "alert"
        html += f"""
        <div class="{alert_class}">
            <strong>{alert.get('category', 'N/A')}</strong><br>
            Speso: €{alert.get('spent', 0):,.2f} / Budget: €{alert.get('budget', 0):,.2f}<br>
            <small>{alert.get('percentage', 0):.1f}% del budget utilizzato</small>
        </div>
        """

    return html


def send_budget_alert_email(recipient_email, alert_data):
    """
    Invia email di alert quando il budget sta per essere superato

    Args:
        recipient_email: Email destinatario
        alert_data: Dict con dati dell'alert

    Returns:
        True se invio riuscito, False altrimenti
    """
    try:
        if 'email' not in st.secrets:
            return False

        sender_email = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = f"⚠️ Alert Budget: {alert_data.get('category', 'N/A')}"

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .alert-box {{
                    background: #fff3cd;
                    border: 2px solid #ffc107;
                    border-radius: 8px;
                    padding: 30px;
                    text-align: center;
                }}
                .critical {{
                    background: #f8d7da;
                    border-color: #dc3545;
                }}
            </style>
        </head>
        <body>
            <div class="alert-box {'critical' if alert_data.get('severity') == 'critical' else ''}">
                <h1>⚠️ Alert Budget</h1>
                <h2>{alert_data.get('category', 'N/A')}</h2>
                <p style="font-size: 24px; margin: 20px 0;">
                    <strong>{alert_data.get('percentage', 0):.1f}%</strong> del budget utilizzato
                </p>
                <p>
                    Speso: <strong>€{alert_data.get('spent', 0):,.2f}</strong><br>
                    Budget: <strong>€{alert_data.get('budget', 0):,.2f}</strong><br>
                    Rimanente: <strong>€{alert_data.get('remaining', 0):,.2f}</strong>
                </p>
                <p style="margin-top: 30px; color: #666;">
                    Controlla le tue spese nell'app per maggiori dettagli.
                </p>
            </div>
        </body>
        </html>
        """

        message.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(message)

        return True

    except Exception as e:
        st.error(f"Errore nell'invio alert: {str(e)}")
        return False


def configure_email_settings():
    """Interfaccia per configurare le impostazioni email"""
    st.subheader("📧 Configurazione Email")

    st.info("""
    Per inviare email automatiche, devi configurare un account Gmail:

    1. Vai su [Google Account](https://myaccount.google.com/)
    2. Vai a Sicurezza > Verifica in due passaggi
    3. In fondo, clicca su "Password per le app"
    4. Genera una nuova password per "Mail"
    5. Copia la password generata

    Poi, aggiungi queste impostazioni in `.streamlit/secrets.toml`:

    ```toml
    [email]
    sender = "tua-email@gmail.com"
    password = "password-app-generata"
    ```
    """)

    # Test email
    with st.expander("🧪 Test Configurazione Email"):
        test_recipient = st.text_input("Email di test", placeholder="test@example.com")

        if st.button("Invia Email di Test"):
            if test_recipient:
                test_data = {
                    'month': datetime.now().strftime('%B %Y'),
                    'total': 1234.56,
                    'transaction_count': 42,
                    'daily_average': 41.15,
                    'top_categories_html': '<p>Test categorie</p>',
                    'recommendations': '<p>Questo è un test!</p>',
                    'alerts': []
                }

                with st.spinner("Invio email di test..."):
                    if send_monthly_report(test_recipient, test_data):
                        st.success("✅ Email inviata con successo!")
                    else:
                        st.error("❌ Errore nell'invio. Controlla la configurazione.")
            else:
                st.warning("Inserisci un indirizzo email")
