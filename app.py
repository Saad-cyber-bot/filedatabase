import streamlit as st
from file_database import SessionLocal, File
import datetime
import os
import pandas as pd
import io
import smtplib
from email.message import EmailMessage


ADMIN_PASSWORD = "superadmin123"
USER_PASSWORD = "hemmelig123"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
        st.session_state["role"] = ""

    def password_entered():
        pw = st.session_state.get("password", "")
        if pw == ADMIN_PASSWORD:
            st.session_state["password_correct"] = True
            st.session_state["role"] = "admin"
        elif pw == USER_PASSWORD:
            st.session_state["password_correct"] = True
            st.session_state["role"] = "user"
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.text_input("🔐 Skriv inn passord:", type="password", key="password", on_change=password_entered)
        if st.session_state.get("password") and not st.session_state["password_correct"]:
            st.error("⛔ Feil passord!")
        st.stop()

check_password()


def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in [".pdf"]:
        return "PDF"
    elif ext in [".jpg", ".jpeg", ".png", ".gif"]:
        return "Bilde"
    elif ext in [".txt"]:
        return "Tekstfil"
    else:
        return "Annet"

st.title("Filopplasting til Database")


# --- Funksjon for å lagre fil ---
def save_file_to_db(name, data):
    db = SessionLocal()
    new_file = File(name=name, data=data)
    db.add(new_file)
    db.commit()
    db.close()

def send_email_with_attachment(to_email, file_data, filename):
    msg = EmailMessage()
    msg['Subject'] = 'Din filrapport'
    sender_email = 'dinadresse@gmail.com'
    msg['From'] = sender_email  # <-- endre til din avsenderadresse
    msg['To'] = to_email
    msg.set_content('Hei! Her er rapporten over opplastede filer.')

    msg.add_attachment(file_data, maintype='application',
                       subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                       filename=filename)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('saadjawoda17@gmail.com', 'vfpv yxyk tpja eicc')  # <-- bytt dette
        smtp.send_message(msg)

# --- Opplasting ---
uploaded_file = st.file_uploader("Last opp en fil")

if uploaded_file is not None:
    file_data = uploaded_file.read()
    save_file_to_db(uploaded_file.name, file_data)
    st.success(f"Filen '{uploaded_file.name}' er lagret i databasen!")

#--- Vise opplastede filer ---
st.subheader("Opplastede filer")

# Søkefelt og sortering
col_sort, col_search = st.columns([1, 3])

with col_search:
    search_query = st.text_input("🔎 Søk etter filnavn")

with col_sort:
    sort_order = st.selectbox("Sorter etter", ["Nyeste først", "Eldste først"])


    

# Hent filer fra databasen
db = SessionLocal()
files = db.query(File).all()
db.close()

# Statistikk
total_files = len(files)
type_counts = {
    "PDF": 0,
    "Bilde": 0,
    "Tekstfil": 0,
    "Annet": 0
}
latest_upload = None

for f in files:
    ftype = get_file_type(f.name)
    type_counts[ftype] += 1
    if not latest_upload or f.upload_date > latest_upload:
        latest_upload = f.upload_date

st.markdown("### 📊 Statistikk")
st.write(f"**Totalt antall filer:** {total_files}")
st.write(f"**Siste opplasting:** {latest_upload.strftime('%Y-%m-%d %H:%M:%S') if latest_upload else 'Ingen filer ennå'}")

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("📄 PDF", type_counts['PDF'])
col_b.metric("🖼️ Bilder", type_counts['Bilde'])
col_c.metric("📝 Tekstfiler", type_counts['Tekstfil'])
col_d.metric("🎲 Annet", type_counts['Annet'])

# Finn alle tilgjengelige filtyper
file_types = list(set(get_file_type(f.name) for f in files))
file_types.sort()
file_types.insert(0, "Alle")


# Sorter filene etter valgt rekkefølge
if sort_order == "Nyeste først":
    files.sort(key=lambda f: f.upload_date, reverse=True)
else:
    files.sort(key=lambda f: f.upload_date)

selected_type = st.selectbox("📁 Filtypefilter", file_types)

#Filtrering hvis søk er skrever inn
if search_query:
    files = [f for f in files if search_query.lower() in f.name.lower()]

if selected_type != "Alle":
    files = [f for f in files if get_file_type(f.name) == selected_type]

# Lag DataFrame for rapport
report_data = [{
    "Filnavn": f.name,
    "Opplastingsdato": f.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
    "Filtype": get_file_type(f.name)
} for f in files]

df_report = pd.DataFrame(report_data)

# Last ned rapport som Excel
if not df_report.empty:
    output = io.BytesIO()

#Send rapport til e-post
st.markdown("### 📧 Send rapport på e-post")

receiver_email = st.text_input("Mottakers e-postadresse")
if st.button("Send rapport"):
    if receiver_email and not df_report.empty:
        try:
            send_email_with_attachment(receiver_email, output.getvalue(), "filrapport.xlsx")
            st.success(f"Rapport sendt til {receiver_email}!")
        except Exception as e:
            st.error(f"Noe gikk galt: {e}")
    else:
        st.warning("Skriv inn en gyldig e-post og sørg for at rapporten ikke er tom.")

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_report.to_excel(writer, index=False, sheet_name='Rapport')
    st.download_button(
        label="📥 Last ned rapport (Excel)",
        data=output.getvalue(),
        file_name="filrapport.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if files:
    for f in files:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.text(f"🗂️ {f.name} (lastet opp {f.upload_date.strftime('%Y-%m-%d %H:%M:%S')})")
        with col2:
            st.download_button("Last ned", f.data, file_name=f.name, key=f"download_{f.id}")
        with col3:
             if st.button(f"Slett", key=f"id_{f.id}"):
                 db.delete(f)
                 db.commit()
                 st.experimental_rerun()
             else:
                st.write("Ingen filer er lastet opp ennå.")
