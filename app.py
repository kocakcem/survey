import os
import sqlite3
import pandas as pd
from io import BytesIO
import streamlit as st

###############################################################################
# CSS Hack to hide the dummy "None" item from the dropdown/radio list
###############################################################################
st.markdown("""
<style>
/* Hide the first (index=0) item in any selectbox dropdown */
[data-baseweb="select"] li:nth-child(1) {
    display: none !important;
}
/* Hide the first (index=0) radio option */
[data-baseweb="radio"] div[role="radio"]:nth-child(1) {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

###############################################################################
# Database Setup
###############################################################################
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

###############################################################################
# Session State Initialization
###############################################################################
if "step" not in st.session_state:
    st.session_state.step = 0  # steps: 0..3, then 4 => "thank you"

# Q1: year_debt => store as "" if unselected
if "year_debt" not in st.session_state:
    st.session_state.year_debt = ""

# Q2: company_scale => store None if unselected
if "company_scale" not in st.session_state:
    st.session_state.company_scale = None

# Q3: debt_amount => store None if unselected
if "debt_amount" not in st.session_state:
    st.session_state.debt_amount = None

# Q4: market_served => store None if unselected
if "market_served" not in st.session_state:
    st.session_state.market_served = None

###############################################################################
# Helper: Save to DB
###############################################################################
def save_response():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO responses (year_debt, company_scale, debt_amount, market_served)
        VALUES (?, ?, ?, ?)
    """, (
        st.session_state.year_debt,
        st.session_state.company_scale,
        st.session_state.debt_amount,
        st.session_state.market_served
    ))
    conn.commit()
    conn.close()

###############################################################################
# Survey Flow
###############################################################################
def survey_page():
    st.title("Şirket Borç Durumu Anketi")

    # Progress bar: step=0..4 => 0%,25%,50%,75%,100%
    progress_val = int((st.session_state.step / 4) * 100)
    st.progress(progress_val)
    st.write(f"{progress_val}% tamamlandı")

    # ========================= STEP 0 =========================
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")
        st.write("Aşağıdaki seçeneklerden birine tıklayın:")

        # 6 buttons for the year
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

        # Show chosen
        if st.session_state.year_debt:
            st.success(f"Seçtiğiniz: {st.session_state.year_debt}")
        else:
            st.info("Henüz bir yıl seçmediniz.")

        # Devam is disabled if no year chosen
        if st.button("Devam", disabled=(st.session_state.year_debt == ""), key="step0_next"):
            st.session_state.step = 1

    # ========================= STEP 1 =========================
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")

        # Updated: we add numbering 1., 2., 3., 4. to the valid options
        scale_choices = [
            None,  # hidden by CSS, "no selection" placeholder
            "1. Mikro ölçekli işletme (1-9 çalışan)",
            "2. Küçük ölçekli işletme (10-49 çalışan)",
            "3. Orta ölçekli işletme (50-250 çalışan)",
            "4. Büyük ölçekli işletme (250 üzeri çalışan)"
        ]

        if st.session_state.company_scale in scale_choices:
            current_index = scale_choices.index(st.session_state.company_scale)
        else:
            current_index = 0  # no selection

        selected = st.selectbox(
            "Seçiniz",
            scale_choices,
            index=current_index,
            key="company_scale_selectbox",
            format_func=lambda x: x if x else ""
        )

        st.session_state.company_scale = selected

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="step1_back"):
            st.session_state.step = 0

        # Devam disabled if user hasn't picked a real choice
        if col_next.button("Devam", disabled=(st.session_state.company_scale is None), key="step1_next"):
            st.session_state.step = 2

    # ========================= STEP 2 =========================
    elif st.session_state.step == 2:
        st.subheader("C. Firmanızın borç oranı nedir?")

        debt_choices = [
            None,  # hidden by CSS
            "0-1 milyon TL",
            "1-5 milyon TL",
            "5-10 milyon TL",
            "10-50 milyon TL",
            "50 milyon TL ve üzeri",
            "Belirtmek istemiyorum"
        ]

        if st.session_state.debt_amount in debt_choices:
            current_index = debt_choices.index(st.session_state.debt_amount)
        else:
            current_index = 0

        chosen = st.radio(
            "Seçiniz",
            debt_choices,
            index=current_index,
            key="debt_amount_radio",
            format_func=lambda x: x if x else ""
        )
        st.session_state.debt_amount = chosen

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="step2_back"):
            st.session_state.step = 1

        if col_next.button("Devam", disabled=(st.session_state.debt_amount is None), key="step2_next"):
            st.session_state.step = 3

    # ========================= STEP 3 =========================
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")

        market_choices = [
            None,  # hidden by CSS
            "Sadece yurtiçi pazara hizmet veriyorum",
            "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
            "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
            "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
            "Sadece yurtdışı pazara hizmet veriyorum"
        ]

        if st.session_state.market_served in market_choices:
            current_index = market_choices.index(st.session_state.market_served)
        else:
            current_index = 0

        selection = st.selectbox(
            "Seçiniz",
            market_choices,
            index=current_index,
            key="market_served_selectbox",
            format_func=lambda x: x if x else ""
        )
        st.session_state.market_served = selection

        col_back, col_submit = st.columns(2)
        if col_back.button("Geri", key="step3_back"):
            st.session_state.step = 2

        if col_submit.button("Gönder", disabled=(st.session_state.market_served is None), key="submit_btn"):
            save_response()
            st.session_state.step = 4

    # ========================= STEP 4: Thank You =========================
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
            st.session_state.company_scale = None
            st.session_state.debt_amount = None
            st.session_state.market_served = None

###############################################################################
# Download Page
###############################################################################
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

###############################################################################
# Main App
###############################################################################
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))

if page == "Anket":
    survey_page()
else:
    download_page()
