import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO

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

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'year_debt' not in st.session_state:
    st.session_state.year_debt = ""
if 'company_scale' not in st.session_state:
    st.session_state.company_scale = ""
if 'debt_amount' not in st.session_state:
    st.session_state.debt_amount = ""
if 'market_served' not in st.session_state:
    st.session_state.market_served = ""

def save_response():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO responses (year_debt, company_scale, debt_amount, market_served) VALUES (?, ?, ?, ?)",
        (st.session_state.year_debt,
         st.session_state.company_scale,
         st.session_state.debt_amount,
         st.session_state.market_served)
    )
    conn.commit()
    conn.close()

def survey_page():
    st.title("Şirket Borç Durumu Anketi")
    # Show progress
    progress = int(((st.session_state.step + 1) / 4) * 100) if st.session_state.step < 4 else 100
    st.progress(progress)

    # -------------- STEP 0 --------------
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")
        # Year buttons
        options = [
            "2000 ve öncesi", "2001-2005 arası", "2006-2010 arası",
            "2011-2015 arası", "2016-2020 arası", "2020-2024 arası"
        ]
        cols = st.columns(3)
        for i in range(3):
            if cols[i].button(options[i], key=f"year_btn_{i}"):
                st.session_state.year_debt = options[i]

        cols = st.columns(3)
        for i in range(3, 6):
            if cols[i-3].button(options[i], key=f"year_btn_{i}"):
                st.session_state.year_debt = options[i]

        if st.session_state.year_debt:
            st.success(f"Seçtiğiniz: {st.session_state.year_debt}")
            if st.button("Devam", key="next1"):
                st.session_state.step += 1
        else:
            st.info("Lütfen bir seçenek belirleyiniz.")

    # -------------- STEP 1 --------------
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")
        options = [
            "Mikro ölçekli işletme (1-9 çalışan)",
            "Küçük ölçekli işletme (10-49 çalışan)",
            "Orta ölçekli işletme (50-250 çalışan)",
            "Büyük ölçekli işletme (250 üzeri çalışan)"
        ]
        selection = st.selectbox("Seçiniz", [""] + options, key="company_scale_select")
        if selection != "":
            st.session_state.company_scale = selection

        col1, col2 = st.columns(2)
        if col1.button("Geri", key="back1"):
            st.session_state.step -= 1

        devam2_clicked = col2.button("Devam", key="next2")
        if devam2_clicked:
            if st.session_state.company_scale:
                st.session_state.step += 1
            else:
                st.error("Lütfen bir seçenek belirleyin.")

    # -------------- STEP 2 --------------
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
        selection = st.radio("Seçiniz", options, key="debt_radio")
        st.session_state.debt_amount = selection

        col1, col2 = st.columns(2)
        if col1.button("Geri", key="back2"):
            st.session_state.step -= 1

        if col2.button("Devam", key="next3"):
            st.session_state.step += 1

    # -------------- STEP 3 --------------
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")
        options = [
            "Sadece yurtiçi pazara hizmet veriyorum",
            "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
            "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
            "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
            "Sadece yurtdışı pazara hizmet veriyorum"
        ]
        selection = st.selectbox("Seçiniz", [""] + options, key="market_select")
        if selection != "":
            st.session_state.market_served = selection

        col1, col2 = st.columns(2)
        if col1.button("Geri", key="back3"):
            st.session_state.step -= 1

        if col2.button("Gönder", key="submit_btn"):
            if st.session_state.market_served:
                save_response()
                st.session_state.step = 4
            else:
                st.error("Lütfen bir seçenek belirleyin.")

    # -------------- STEP 4 (Thank you) --------------
    elif st.session_state.step == 4:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 50px;">
                <h2 style="color: green;">Teşekkürler!</h2>
                <p>Cevabınız kaydedildi.</p>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Yeni Anket Doldurmak İçin Başla", key="restart"):
            st.session_state.step = 0
            st.session_state.year_debt = ""
            st.session_state.company_scale = ""
            st.session_state.debt_amount = ""
            st.session_state.market_served = ""

def download_page():
    st.title("Anket Sonuçlarını İndir")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Parola", type="password")

    admin_username = os.environ.get("ADMIN_USERNAME", "user.vision")
    admin_password = os.environ.get("ADMIN_PASSWORD", "cemisthe.bestfreelancer.ever")

    if st.button("Giriş Yap", key="login_btn"):
        if username == admin_username and password == admin_password:
            st.success("Giriş başarılı!")
            conn = sqlite3.connect(DATABASE)
            df = pd.read_sql_query("SELECT * FROM responses", conn)
            conn.close()
            st.write(df)
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
            st.error("Hatalı kullanıcı adı/parola.")

# Sidebar
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))

if page == "Anket":
    survey_page()
else:
    download_page()
