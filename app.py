import os
import sqlite3
import pandas as pd
from io import BytesIO
import streamlit as st

# ------------------------------------
# Database Setup
# ------------------------------------
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

# ------------------------------------
# Session State Initialization
# ------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0  # steps: 0 to 3; 4 is "submitted"

# For each question, the answer is stored as an empty string initially.
if "year_debt" not in st.session_state:
    st.session_state.year_debt = ""
if "company_scale" not in st.session_state:
    st.session_state.company_scale = ""
if "debt_amount" not in st.session_state:
    st.session_state.debt_amount = ""
if "market_served" not in st.session_state:
    st.session_state.market_served = ""

# ------------------------------------
# Helper: Save Response to DB
# ------------------------------------
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

# ------------------------------------
# Survey Page
# ------------------------------------
def survey_page():
    st.title("Şirket Borç Durumu Anketi")
    # Compute progress: step 0 to 4 maps to 0%, 25%, 50%, 75%, 100%
    progress_val = (st.session_state.step / 4) * 100
    st.progress(progress_val)
    st.write(f"{int(progress_val)}% tamamlandı")

    # ----- STEP 0: Year of Highest Debt -----
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")
        st.write("Lütfen aşağıdaki seçeneklerden birine tıklayın:")
        # Show answer options as buttons (no auto‑selection)
        options = [
            "2000 ve öncesi",
            "2001-2005 arası",
            "2006-2010 arası",
            "2011-2015 arası",
            "2016-2020 arası",
            "2020-2024 arası"
        ]
        cols = st.columns(3)
        # Display first three options in first row…
        for i, option in enumerate(options[:3]):
            if cols[i].button(option, key=f"year_btn_{i}"):
                st.session_state.year_debt = option
        # …and the next three in a second row.
        cols2 = st.columns(3)
        for i, option in enumerate(options[3:]):
            if cols2[i].button(option, key=f"year_btn_{i+3}"):
                st.session_state.year_debt = option

        st.write("Seçtiğiniz: ", st.session_state.year_debt)
        # Continue button: enabled only if a selection has been made.
        if st.button("Devam", disabled=(st.session_state.year_debt == ""), key="next0"):
            st.session_state.step = 1

    # ----- STEP 1: Company Scale -----
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")
        # Use a selectbox with an empty initial value
        options = ["Mikro ölçekli işletme (1-9 çalışan)",
                   "Küçük ölçekli işletme (10-49 çalışan)",
                   "Orta ölçekli işletme (50-250 çalışan)",
                   "Büyük ölçekli işletme (250 üzeri çalışan)"]
        # Build list with an empty placeholder (which is not a valid answer)
        select_options = [""] + options
        # If a value was previously chosen, use it as the default (else index 0)
        default_index = select_options.index(st.session_state.company_scale) if st.session_state.company_scale in select_options else 0
        chosen = st.selectbox("Seçiniz", select_options, index=default_index, key="company_scale_select")
        st.session_state.company_scale = chosen

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back1"):
            st.session_state.step = 0
        if col_next.button("Devam", disabled=(st.session_state.company_scale == ""), key="next1"):
            st.session_state.step = 2

    # ----- STEP 2: Debt Amount -----
    elif st.session_state.step == 2:
        st.subheader("C. Firmanızın borç oranı nedir?")
        options = ["0-1 milyon TL",
                   "1-5 milyon TL",
                   "5-10 milyon TL",
                   "10-50 milyon TL",
                   "50 milyon TL ve üzeri",
                   "Belirtmek istemiyorum"]
        select_options = [""] + options
        default_index = select_options.index(st.session_state.debt_amount) if st.session_state.debt_amount in select_options else 0
        chosen = st.selectbox("Seçiniz", select_options, index=default_index, key="debt_amount_select")
        st.session_state.debt_amount = chosen

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back2"):
            st.session_state.step = 1
        if col_next.button("Devam", disabled=(st.session_state.debt_amount == ""), key="next2"):
            st.session_state.step = 3

    # ----- STEP 3: Market Served -----
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")
        options = ["Sadece yurtiçi pazara hizmet veriyorum",
                   "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
                   "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
                   "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazarlara hizmet veriyorum",
                   "Sadece yurtdışı pazara hizmet veriyorum"]
        select_options = [""] + options
        default_index = select_options.index(st.session_state.market_served) if st.session_state.market_served in select_options else 0
        chosen = st.selectbox("Seçiniz", select_options, index=default_index, key="market_served_select")
        st.session_state.market_served = chosen

        col_back, col_submit = st.columns(2)
        if col_back.button("Geri", key="back3"):
            st.session_state.step = 2
        if col_submit.button("Gönder", disabled=(st.session_state.market_served == ""), key="submit"):
            save_response()
            st.session_state.step = 4

    # ----- STEP 4: Thank You Page -----
    elif st.session_state.step == 4:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 50px;">
                <h2 style="color: green;">Teşekkürler!</h2>
                <p>Cevabınız kaydedildi.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Yeni Anket Doldurmak İçin Başla", key="restart"):
            st.session_state.step = 0
            st.session_state.year_debt = ""
            st.session_state.company_scale = ""
            st.session_state.debt_amount = ""
            st.session_state.market_served = ""

# ------------------------------------
# Download Page
# ------------------------------------
def download_page():
    st.title("Anket Sonuçlarını İndir")
    st.write("Lütfen yetkilendirme bilgilerinizi giriniz.")
    username = st.text_input("Kullanıcı Adı", key="username")
    password = st.text_input("Parola", type="password", key="password")
    admin_username = os.environ.get("ADMIN_USERNAME", "user.vision")
    admin_password = os.environ.get("ADMIN_PASSWORD", "cemisthe.bestfreelancer.ever")
    if st.button("Giriş Yap", key="login"):
        if username == admin_username and password == admin_password:
            st.success("Giriş başarılı!")
            conn = sqlite3.connect(DATABASE)
            df = pd.read_sql_query("SELECT * FROM responses", conn)
            conn.close()
            st.write("Kayıtlı cevaplar:")
            st.dataframe(df)
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

# ------------------------------------
# Main Navigation via Sidebar
# ------------------------------------
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))
if page == "Anket":
    survey_page()
else:
    download_page()
