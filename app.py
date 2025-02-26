import os
import sqlite3
import pandas as pd
from io import BytesIO
import streamlit as st

# -----------------------------------------------------
# Database Setup
# -----------------------------------------------------
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

# -----------------------------------------------------
# Session State Initialization
# -----------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0  # steps: 0..3, then 4 = "thank you" page

# Survey answers stored in session_state so we don't lose them on page refresh
if "year_debt" not in st.session_state:
    st.session_state.year_debt = ""
if "company_scale" not in st.session_state:
    st.session_state.company_scale = ""
if "debt_amount" not in st.session_state:
    st.session_state.debt_amount = ""
if "market_served" not in st.session_state:
    st.session_state.market_served = ""

# -----------------------------------------------------
# Helper: Write response to DB
# -----------------------------------------------------
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

# -----------------------------------------------------
# Survey Pages
# -----------------------------------------------------
def survey_page():
    st.title("Şirket Borç Durumu Anketi")

    # ---- Progress Bar ----
    # Step can be 0..4; we map that to 0..100% in increments of 25
    # 0 -> 0%, 1 -> 25%, 2 -> 50%, 3 -> 75%, 4 -> 100%
    progress_val = min(st.session_state.step, 4) * 25
    st.progress(progress_val)
    st.write(f"{progress_val}% tamamlandı")

    # -------------- STEP 0: Year of Highest Debt --------------
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")
        st.write("Aşağıdaki seçeneklerden birini seçin:")

        # We store the user's selection in session_state.year_debt
        # We'll replicate the "buttons" approach from your original code.
        options = [
            "2000 ve öncesi",
            "2001-2005 arası",
            "2006-2010 arası",
            "2011-2015 arası",
            "2016-2020 arası",
            "2020-2024 arası"
        ]

        # Show them in two rows of 3
        row1 = st.columns(3)
        for i in range(3):
            if row1[i].button(options[i], key=f"year_btn_{i}"):
                st.session_state.year_debt = options[i]

        row2 = st.columns(3)
        for i in range(3, 6):
            if row2[i-3].button(options[i], key=f"year_btn_{i}"):
                st.session_state.year_debt = options[i]

        # Display the chosen selection (if any)
        if st.session_state.year_debt:
            st.success(f"Seçtiğiniz: {st.session_state.year_debt}")

        # Navigation
        col_next = st.columns([1,1,5])[0]  # Just a small column for alignment
        if col_next.button("Devam", key="next1"):
            if st.session_state.year_debt:
                st.session_state.step = 1
            else:
                st.warning("Lütfen bir yıl seçiniz.")

    # -------------- STEP 1: Company Scale --------------
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")
        options = [
            "Mikro ölçekli işletme (1-9 çalışan)",
            "Küçük ölçekli işletme (10-49 çalışan)",
            "Orta ölçekli işletme (50-250 çalışan)",
            "Büyük ölçekli işletme (250 üzeri çalışan)"
        ]

        # Use a selectbox with no empty top option
        selection = st.selectbox("Seçiniz", options, key="company_scale_select")

        # Keep the selection in session state
        st.session_state.company_scale = selection

        # Show the user's current choice
        st.success(f"Seçtiğiniz: {st.session_state.company_scale}")

        # Navigation
        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back1"):
            st.session_state.step = 0

        if col_next.button("Devam", key="next2"):
            # Must confirm user picked something
            if st.session_state.company_scale:
                st.session_state.step = 2
            else:
                st.warning("Lütfen bir seçenek belirleyin.")

    # -------------- STEP 2: Debt Amount --------------
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
        # A radio automatically has a default selection unless we give it an index
        # We'll let session_state handle it:
        debt_choice = st.radio("Seçiniz", options, index=options.index(st.session_state.debt_amount) if st.session_state.debt_amount in options else 0, key="debt_radio")
        st.session_state.debt_amount = debt_choice

        # Show chosen
        st.success(f"Seçtiğiniz: {st.session_state.debt_amount}")

        # Navigation
        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back2"):
            st.session_state.step = 1

        if col_next.button("Devam", key="next3"):
            st.session_state.step = 3

    # -------------- STEP 3: Market Served --------------
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")
        options = [
            "Sadece yurtiçi pazara hizmet veriyorum",
            "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
            "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
            "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
            "Sadece yurtdışı pazara hizmet veriyorum"
        ]
        # Another selectbox, no empty top option
        market_choice = st.selectbox("Seçiniz", options, index=options.index(st.session_state.market_served) if st.session_state.market_served in options else 0, key="market_select")
        st.session_state.market_served = market_choice

        st.success(f"Seçtiğiniz: {st.session_state.market_served}")

        # Navigation
        col_back, col_submit = st.columns(2)
        if col_back.button("Geri", key="back3"):
            st.session_state.step = 2

        if col_submit.button("Gönder", key="submit_btn"):
            # Save to DB
            if st.session_state.market_served:
                save_response()
                st.session_state.step = 4
            else:
                st.warning("Lütfen bir seçenek belirleyin.")

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
        # Option to reset the survey
        if st.button("Yeni Anket Doldurmak İçin Başla", key="restart"):
            st.session_state.step = 0
            st.session_state.year_debt = ""
            st.session_state.company_scale = ""
            st.session_state.debt_amount = ""
            st.session_state.market_served = ""

# -----------------------------------------------------
# Download Page
# -----------------------------------------------------
def download_page():
    st.title("Anket Sonuçlarını İndir")
    st.write("Lütfen yetkilendirme bilgilerinizi giriniz.")

    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Parola", type="password")

    # Default credentials if environment variables not set
    admin_username = os.environ.get("ADMIN_USERNAME", "user.vision")
    admin_password = os.environ.get("ADMIN_PASSWORD", "cemisthe.bestfreelancer.ever")

    if st.button("Giriş Yap", key="login_btn"):
        if username == admin_username and password == admin_password:
            st.success("Giriş başarılı!")

            # Retrieve data from the database
            conn = sqlite3.connect(DATABASE)
            df = pd.read_sql_query("SELECT * FROM responses", conn)
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

# -----------------------------------------------------
# Main Navigation in Sidebar
# -----------------------------------------------------
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))

if page == "Anket":
    survey_page()
else:
    download_page()
