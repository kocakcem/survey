import os
import sqlite3
import pandas as pd
from io import BytesIO
import streamlit as st

# -------------------------------------------------------------------
# Database Setup
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# Session State Defaults
# -------------------------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0  # Steps: 0..3, then 4 => "thank you"

# Each answer starts empty. If empty, the user can't proceed.
if "year_debt" not in st.session_state:
    st.session_state.year_debt = ""
if "company_scale" not in st.session_state:
    st.session_state.company_scale = ""
if "debt_amount" not in st.session_state:
    st.session_state.debt_amount = ""
if "market_served" not in st.session_state:
    st.session_state.market_served = ""

# -------------------------------------------------------------------
# Helper: Save Response to DB
# -------------------------------------------------------------------
def save_response():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO responses (year_debt, company_scale, debt_amount, market_served) VALUES (?, ?, ?, ?)",
        (
            st.session_state.year_debt,
            st.session_state.company_scale,
            st.session_state.debt_amount,
            st.session_state.market_served
        )
    )
    conn.commit()
    conn.close()

# -------------------------------------------------------------------
# Survey Flow
# -------------------------------------------------------------------
def survey_page():
    st.title("Şirket Borç Durumu Anketi")

    # Progress bar: step=0..4 => 0%,25%,50%,75%,100%
    progress_val = int((st.session_state.step / 4) * 100)
    st.progress(progress_val)
    st.write(f"{progress_val}% tamamlandı")

    # -------------- STEP 0: Year Debt (6 Buttons) --------------
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")
        st.write("Aşağıdaki seçeneklerden birine tıklayın:")

        # 6 possible buttons in two rows of 3
        year_options = [
            "2000 ve öncesi",
            "2001-2005 arası",
            "2006-2010 arası",
            "2011-2015 arası",
            "2016-2020 arası",
            "2020-2024 arası"
        ]

        row1 = st.columns(3)
        for i, opt in enumerate(year_options[:3]):
            if row1[i].button(opt, key=f"year_btn_{i}"):
                st.session_state.year_debt = opt

        row2 = st.columns(3)
        for i, opt in enumerate(year_options[3:], start=3):
            if row2[i-3].button(opt, key=f"year_btn_{i}"):
                st.session_state.year_debt = opt

        # Show user’s choice
        if st.session_state.year_debt:
            st.success(f"Seçtiğiniz: {st.session_state.year_debt}")
        else:
            st.info("Henüz bir yıl seçmediniz.")

        # "Devam" is disabled if no year chosen
        if st.button("Devam", disabled=(st.session_state.year_debt == ""), key="step0_next"):
            st.session_state.step = 1

    # -------------- STEP 1: Company Scale (Selectbox) --------------
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")

        # The user sees a selectbox with a blank top entry (no text).
        # That blank entry is not valid. If the user is on the blank entry,
        # st.session_state.company_scale remains "".
        scale_options = [
            "Mikro ölçekli işletme (1-9 çalışan)",
            "Küçük ölçekli işletme (10-49 çalışan)",
            "Orta ölçekli işletme (50-250 çalışan)",
            "Büyük ölçekli işletme (250 üzeri çalışan)"
        ]
        # We'll prepend an empty string. We also use a format_func so it appears truly blank in the dropdown.
        full_options = [""] + scale_options

        # figure out which index to show based on session_state
        if st.session_state.company_scale in scale_options:
            current_index = scale_options.index(st.session_state.company_scale) + 1
        else:
            current_index = 0  # blank

        selection = st.selectbox(
            "Seçiniz",
            full_options,
            index=current_index,
            format_func=lambda x: x if x else "",
            key="company_scale_selectbox"
        )

        # If the user picks the blank line => st.session_state.company_scale = ""
        # Otherwise store the real choice
        if selection == "":
            st.session_state.company_scale = ""
        else:
            st.session_state.company_scale = selection

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="step1_back"):
            st.session_state.step = 0

        if col_next.button("Devam", disabled=(st.session_state.company_scale == ""), key="step1_next"):
            st.session_state.step = 2

    # -------------- STEP 2: Debt Amount (Radio) --------------
    elif st.session_state.step == 2:
        st.subheader("C. Firmanızın borç oranı nedir?")

        debt_options = [
            "0-1 milyon TL",
            "1-5 milyon TL",
            "5-10 milyon TL",
            "10-50 milyon TL",
            "50 milyon TL ve üzeri",
            "Belirtmek istemiyorum"
        ]
        # We'll add a blank at the top so there's no default.
        full_debt_options = [""] + debt_options

        # figure out which index to show
        if st.session_state.debt_amount in debt_options:
            current_index = debt_options.index(st.session_state.debt_amount) + 1
        else:
            current_index = 0

        chosen = st.radio(
            "Seçiniz",
            full_debt_options,
            index=current_index,
            format_func=lambda x: x if x else "",
            key="debt_amount_radio"
        )

        if chosen == "":
            st.session_state.debt_amount = ""
        else:
            st.session_state.debt_amount = chosen

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="step2_back"):
            st.session_state.step = 1

        if col_next.button("Devam", disabled=(st.session_state.debt_amount == ""), key="step2_next"):
            st.session_state.step = 3

    # -------------- STEP 3: Market Served (Selectbox) --------------
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")

        market_options = [
            "Sadece yurtiçi pazara hizmet veriyorum",
            "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
            "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
            "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
            "Sadece yurtdışı pazara hizmet veriyorum"
        ]
        full_market_options = [""] + market_options

        if st.session_state.market_served in market_options:
            current_index = market_options.index(st.session_state.market_served) + 1
        else:
            current_index = 0

        selection = st.selectbox(
            "Seçiniz",
            full_market_options,
            index=current_index,
            format_func=lambda x: x if x else "",
            key="market_served_selectbox"
        )

        if selection == "":
            st.session_state.market_served = ""
        else:
            st.session_state.market_served = selection

        col_back, col_submit = st.columns(2)
        if col_back.button("Geri", key="step3_back"):
            st.session_state.step = 2

        if col_submit.button("Gönder", disabled=(st.session_state.market_served == ""), key="submit_btn"):
            # Save to DB
            save_response()
            st.session_state.step = 4

    # -------------- STEP 4: Thank You --------------
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
            # Reset
            st.session_state.step = 0
            st.session_state.year_debt = ""
            st.session_state.company_scale = ""
            st.session_state.debt_amount = ""
            st.session_state.market_served = ""

# -------------------------------------------------------------------
# Download Page
# -------------------------------------------------------------------
def download_page():
    st.title("Anket Sonuçlarını İndir")
    st.write("Lütfen yetkilendirme bilgilerinizi giriniz.")

    username = st.text_input("Kullanıcı Adı", key="username")
    password = st.text_input("Parola", type="password", key="password")

    admin_username = os.environ.get("ADMIN_USERNAME", "user.vision")
    admin_password = os.environ.get("ADMIN_PASSWORD", "cemisthe.bestfreelancer.ever")

    if st.button("Giriş Yap", key="login_btn"):
        if username == admin_username and password == admin_password:
            st.success("Giriş başarılı!")
            conn = sqlite3.connect(DATABASE)
            df = pd.read_sql_query("SELECT * FROM responses", conn)
            conn.close()

            st.write("Kayıtlı cevaplar:")
            st.dataframe(df)

            # Convert to Excel
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

# -------------------------------------------------------------------
# Main App
# -------------------------------------------------------------------
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))

if page == "Anket":
    survey_page()
else:
    download_page()
