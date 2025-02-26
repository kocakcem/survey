import os
import sqlite3
import pandas as pd
from io import BytesIO
import streamlit as st

# -------------------------------
# Database Setup
# -------------------------------
DATABASE = "survey.db"

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

# -------------------------------
# Session State Initialization
# -------------------------------
if 'step' not in st.session_state:
    st.session_state.step = 0  # survey page: 0 to 3; 4 = submitted
if 'year_debt' not in st.session_state:
    st.session_state.year_debt = ""
if 'company_scale' not in st.session_state:
    st.session_state.company_scale = ""
if 'debt_amount' not in st.session_state:
    st.session_state.debt_amount = ""
if 'market_served' not in st.session_state:
    st.session_state.market_served = ""

# -------------------------------
# Helper: Write response to DB
# -------------------------------
def save_response():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO responses (year_debt, company_scale, debt_amount, market_served) VALUES (?, ?, ?, ?)",
        (st.session_state.year_debt, st.session_state.company_scale, st.session_state.debt_amount, st.session_state.market_served)
    )
    conn.commit()
    conn.close()

# -------------------------------
# Survey Pages
# -------------------------------
def survey_page():
    st.title("Şirket Borç Durumu Anketi")
    
    # Progress bar (4 questions)
    progress = int(((st.session_state.step + 1) / 4) * 100) if st.session_state.step < 4 else 100
    st.progress(progress)
    st.write(f"{progress}% tamamlandı")
    
    # QUESTION 1: Year Debt
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")
        st.write("Aşağıdaki seçeneklerden birini tıklayın:")
        
        # Arrange buttons in two rows using columns
        options = ["2000 ve öncesi", "2001-2005 arası", "2006-2010 arası", 
                   "2011-2015 arası", "2016-2020 arası", "2020-2024 arası"]
        
        # First row (3 options)
        cols = st.columns(3)
        for i in range(3):
            if cols[i].button(options[i]):
                st.session_state.year_debt = options[i]
        # Second row (3 options)
        cols = st.columns(3)
        for i in range(3,6):
            if cols[i-3].button(options[i]):
                st.session_state.year_debt = options[i]
                
        if st.session_state.year_debt:
            st.success(f"Seçtiğiniz: {st.session_state.year_debt}")
            if st.button("Devam"):
                st.session_state.step += 1
        else:
            st.info("Lütfen bir seçenek belirleyiniz.")
            
    # QUESTION 2: Company Scale
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")
        options = [
            "Mikro ölçekli işletme (1-9 çalışan)",
            "Küçük ölçekli işletme (10-49 çalışan)",
            "Orta ölçekli işletme (50-250 çalışan)",
            "Büyük ölçekli işletme (250 üzeri çalışan)"
        ]
        selection = st.selectbox("Seçiniz", [""] + options, index=0)
        if selection != "":
            st.session_state.company_scale = selection
        if st.session_state.company_scale:
            st.success(f"Seçtiğiniz: {st.session_state.company_scale}")
        col1, col2 = st.columns(2)
        if col1.button("Geri"):
            st.session_state.step -= 1
        if col2.button("Devam") and st.session_state.company_scale:
            st.session_state.step += 1
        elif col2.button("Devam") and not st.session_state.company_scale:
            st.error("Lütfen bir seçenek belirleyin.")
            
    # QUESTION 3: Debt Amount (radio buttons)
    elif st.session_state.step == 2:
        st.subheader("C. Firmanızın borç oranı nedir?")
        options = [
            "0-1 milyon TL",
            "1-5 milyon TL",
            "5-10 milyon TL",
            "10-50 milyon TL",
            "50 milyon TL ve üzeri",
            "Belirtmek istemiyorum"
        ]
        selection = st.radio("Seçiniz", options, index=0)
        if selection:
            st.session_state.debt_amount = selection
            st.success(f"Seçtiğiniz: {st.session_state.debt_amount}")
        col1, col2 = st.columns(2)
        if col1.button("Geri"):
            st.session_state.step -= 1
        if col2.button("Devam"):
            st.session_state.step += 1

    # QUESTION 4: Market Served
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")
        options = [
            "Sadece yurtiçi pazara hizmet veriyorum",
            "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
            "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
            "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
            "Sadece yurtdışı pazara hizmet veriyorum"
        ]
        selection = st.selectbox("Seçiniz", [""] + options, index=0)
        if selection != "":
            st.session_state.market_served = selection
        if st.session_state.market_served:
            st.success(f"Seçtiğiniz: {st.session_state.market_served}")
        col1, col2 = st.columns(2)
        if col1.button("Geri"):
            st.session_state.step -= 1
        if col2.button("Gönder"):
            if st.session_state.market_served:
                save_response()
                st.session_state.step = 4  # mark as submitted
            else:
                st.error("Lütfen bir seçenek belirleyin.")
    
    # Submission Complete
    elif st.session_state.step == 4:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 50px;">
                <h2 style="color: green;">Teşekkürler!</h2>
                <p>Cevabınız kaydedildi.</p>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Yeni Anket Doldurmak İçin Başla"):
            # Reset survey state to start over
            st.session_state.step = 0
            st.session_state.year_debt = ""
            st.session_state.company_scale = ""
            st.session_state.debt_amount = ""
            st.session_state.market_served = ""

# -------------------------------
# Download Responses Page (with basic auth)
# -------------------------------
def download_page():
    st.title("Anket Sonuçlarını İndir")
    st.write("Lütfen yetkilendirme bilgilerinizi giriniz.")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Parola", type="password")
    
    admin_username = os.environ.get("ADMIN_USERNAME", "user.vision")
    admin_password = os.environ.get("ADMIN_PASSWORD", "cemisthe.bestfreelancer.ever")
    
    if st.button("Giriş Yap"):
        if username == admin_username and password == admin_password:
            st.success("Giriş başarılı!")
            # Retrieve data from database
            conn = sqlite3.connect(DATABASE)
            df = pd.read_sql_query("SELECT year_debt, company_scale, debt_amount, market_served FROM responses", conn)
            conn.close()
            
            st.write("Kayıtlı cevaplar:")
            st.dataframe(df)
            
            # Create Excel in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Responses")
            output.seek(0)
            
            st.download_button(
                label="Excel Dosyasını İndir",
                data=output,
                file_name="poll_responses.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Geçersiz kullanıcı adı veya parola.")

# -------------------------------
# Main Navigation
# -------------------------------
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))

if page == "Anket":
    survey_page()
else:
    download_page()
