import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO

# Define the SQLite database file
DATABASE = "survey.db"

# Initialize the database and create the table if it doesn't exist
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_debt TEXT,
            company_scale TEXT,
            debt_amount TEXT,
            market_served TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Function to save a survey response to the database
def save_response(year_debt, company_scale, debt_amount, market_served):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO responses (year_debt, company_scale, debt_amount, market_served) VALUES (?, ?, ?, ?)",
              (year_debt, company_scale, debt_amount, market_served))
    conn.commit()
    conn.close()

# Function to load all responses from the database as a DataFrame
def load_responses():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM responses", conn)
    conn.close()
    return df

# Sidebar navigation to switch between the Survey page and the Admin (download) page.
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Survey", "Download Results"])

if page == "Survey":
    st.title("Şirket Borç Durumu Anketi")
    
    # Use a form to group the survey questions
    with st.form("survey_form"):
        # Question 1: Year with most debt
        year_debt = st.radio(
            "A. Firmanızın en çok borçlandığı yıl hangisidir?",
            options=[
                "2000 ve öncesi",
                "2001-2005 arası",
                "2006-2010 arası",
                "2011-2015 arası",
                "2016-2020 arası",
                "2020-2024 arası"
            ]
        )
        
        # Question 2: Company scale
        company_scale = st.selectbox(
            "B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?",
            options=[
                "",
                "Mikro ölçekli işletme (1-9 çalışan)",
                "Küçük ölçekli işletme (10-49 çalışan)",
                "Orta ölçekli işletme (50-250 çalışan)",
                "Büyük ölçekli işletme (250 üzeri çalışan)"
            ]
        )
        
        # Question 3: Debt amount
        debt_amount = st.radio(
            "C. Firmanızın borç oranı nedir?",
            options=[
                "0-1 milyon TL",
                "1-5 milyon TL",
                "5-10 milyon TL",
                "10-50 milyon TL",
                "50 milyon TL ve üzeri",
                "Belirtmek istemiyorum"
            ]
        )
        
        # Question 4: Markets served
        market_served = st.selectbox(
            "D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?",
            options=[
                "",
                "Sadece yurtiçi pazara hizmet veriyorum",
                "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
                "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
                "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
                "Sadece yurtdışı pazara hizmet veriyorum"
            ]
        )
        
        # Form submission button
        submitted = st.form_submit_button("Gönder")
    
    # Validate that all required fields have been filled out
    if submitted:
        if company_scale == "" or market_served == "":
            st.error("Lütfen tüm soruları cevaplayın.")
        else:
            save_response(year_debt, company_scale, debt_amount, market_served)
            st.success("Teşekkürler! Cevabınız kaydedildi.")

elif page == "Download Results":
    st.title("Download Survey Results")
    st.write("Bu sayfa yalnızca yetkili kullanıcılar içindir.")
    
    # Simple authentication: enter username and password
    admin_username = st.text_input("Kullanıcı Adı")
    admin_password = st.text_input("Şifre", type="password")
    
    if st.button("Giriş Yap"):
        # Check against your credentials (change these as needed)
        if admin_username == "user.vision" and admin_password == "cemisthe.bestfreelancer.ever":
            df = load_responses()
            st.subheader("Kayıtlı Yanıtlar")
            st.dataframe(df)
            
            # Convert DataFrame to an Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Responses")
            output.seek(0)
            
            st.download_button(
                label="Excel dosyasını indir",
                data=output,
                file_name="poll_responses.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Giriş başarısız, lütfen tekrar deneyin.")
