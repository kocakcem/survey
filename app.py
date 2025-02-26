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
# Session State Defaults
# ------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0  # 0..3, then 4 = "submitted"

# For each question, store the user's choice. Empty string = no choice yet.
if "year_debt" not in st.session_state:
    st.session_state.year_debt = ""
if "company_scale" not in st.session_state:
    st.session_state.company_scale = ""
if "debt_amount" not in st.session_state:
    st.session_state.debt_amount = ""
if "market_served" not in st.session_state:
    st.session_state.market_served = ""

# ------------------------------------
# Save Response to DB
# ------------------------------------
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

# ------------------------------------
# The Survey
# ------------------------------------
def survey_page():
    st.title("Şirket Borç Durumu Anketi")

    # --- Progress Bar ---
    # step=0..4 => 0%, 25%, 50%, 75%, 100%
    progress_val = int((st.session_state.step / 4) * 100)
    st.progress(progress_val)
    st.write(f"{progress_val}% tamamlandı")

    # ============= STEP 0: Year of Highest Debt =============
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")

        # We'll use a radio with a "Lütfen Seçiniz" placeholder
        # so there's no valid selection by default.
        options = [
            "2000 ve öncesi",
            "2001-2005 arası",
            "2006-2010 arası",
            "2011-2015 arası",
            "2016-2020 arası",
            "2020-2024 arası"
        ]
        # Build the radio with an extra placeholder at the top:
        radio_options = ["Lütfen Seçiniz"] + options

        # Figure out which index to show as selected:
        if st.session_state.year_debt in options:
            # previously chosen a valid item
            default_index = options.index(st.session_state.year_debt) + 1
        else:
            # no choice yet
            default_index = 0

        chosen = st.radio(
            "Seçiniz:",
            radio_options,
            index=default_index,
            key="year_debt_radio"
        )

        # If user picks the placeholder, interpret as no valid choice
        if chosen == "Lütfen Seçiniz":
            st.session_state.year_debt = ""
        else:
            st.session_state.year_debt = chosen

        # "Devam" is disabled if there's no valid choice
        if st.button("Devam", disabled=(st.session_state.year_debt == ""), key="next0"):
            st.session_state.step = 1

    # ============= STEP 1: Company Scale =============
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")

        options = [
            "Mikro ölçekli işletme (1-9 çalışan)",
            "Küçük ölçekli işletme (10-49 çalışan)",
            "Orta ölçekli işletme (50-250 çalışan)",
            "Büyük ölçekli işletme (250 üzeri çalışan)"
        ]
        radio_options = ["Lütfen Seçiniz"] + options

        if st.session_state.company_scale in options:
            default_index = options.index(st.session_state.company_scale) + 1
        else:
            default_index = 0

        chosen = st.radio(
            "Seçiniz:",
            radio_options,
            index=default_index,
            key="company_scale_radio"
        )

        if chosen == "Lütfen Seçiniz":
            st.session_state.company_scale = ""
        else:
            st.session_state.company_scale = chosen

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back1"):
            st.session_state.step = 0

        if col_next.button("Devam", disabled=(st.session_state.company_scale == ""), key="next1"):
            st.session_state.step = 2

    # ============= STEP 2: Debt Amount =============
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
        radio_options = ["Lütfen Seçiniz"] + options

        if st.session_state.debt_amount in options:
            default_index = options.index(st.session_state.debt_amount) + 1
        else:
            default_index = 0

        chosen = st.radio(
            "Seçiniz:",
            radio_options,
            index=default_index,
            key="debt_amount_radio"
        )

        if chosen == "Lütfen Seçiniz":
            st.session_state.debt_amount = ""
        else:
            st.session_state.debt_amount = chosen

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back2"):
            st.session_state.step = 1

        if col_next.button("Devam", disabled=(st.session_state.debt_amount == ""), key="next2"):
            st.session_state.step = 3

    # ============= STEP 3: Market Served =============
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")

        options = [
            "Sadece yurtiçi pazara hizmet veriyorum",
            "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
            "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
            "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
            "Sadece yurtdışı pazara hizmet veriyorum"
        ]
        radio_options = ["Lütfen Seçiniz"] + options

        if st.session_state.market_served in options:
            default_index = options.index(st.session_state.market_served) + 1
        else:
            default_index = 0

        chosen = st.radio(
            "Seçiniz:",
            radio_options,
            index=default_index,
            key="market_served_radio"
        )

        if chosen == "Lütfen Seçiniz":
            st.session_state.market_served = ""
        else:
            st.session_state.market_served = chosen

        col_back, col_submit = st.columns(2)
        if col_back.button("Geri", key="back3"):
            st.session_state.step = 2

        if col_submit.button("Gönder", disabled=(st.session_state.market_served == ""), key="submit_btn"):
            save_response()
            st.session_state.step = 4

    # ============= STEP 4: Thank You =============
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

# ------------------------------------
# Main App
# ------------------------------------
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))

if page == "Anket":
    survey_page()
else:
    download_page()
