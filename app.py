import os
import sqlite3
import pandas as pd
from io import BytesIO
import streamlit as st

# ---------------------------------
# Database Setup
# ---------------------------------
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

# ---------------------------------
# Session State Defaults
# ---------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0  # from 0..3, then 4 = "submitted"

# Answers stored in session state so we don’t lose them:
if "year_debt" not in st.session_state:
    st.session_state.year_debt = ""  # no choice
if "company_scale" not in st.session_state:
    st.session_state.company_scale = ""  # no choice
if "debt_amount" not in st.session_state:
    st.session_state.debt_amount = ""  # no choice
if "market_served" not in st.session_state:
    st.session_state.market_served = ""  # no choice

# ---------------------------------
# Save Response
# ---------------------------------
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

# ---------------------------------
# Survey Pages
# ---------------------------------
def survey_page():
    st.title("Şirket Borç Durumu Anketi")

    # Progress bar: step=0..4 => 0%, 25%, 50%, 75%, 100%
    progress_val = int((st.session_state.step / 4) * 100)
    st.progress(progress_val)
    st.write(f"{progress_val}% tamamlandı")

    # ============= STEP 0 =============
    if st.session_state.step == 0:
        st.subheader("A. Firmanızın en çok borçlandığı yıl hangisidir?")
        st.write("Aşağıdaki düğmelerden birini tıklayın:")

        # Show 6 buttons in two rows. Once user clicks a button, we store that choice in session_state.year_debt.
        # That automatically re-runs the script, enabling the "Devam" button in the next render.
        row1 = st.columns(3)
        year_options = [
            "2000 ve öncesi",
            "2001-2005 arası",
            "2006-2010 arası",
            "2011-2015 arası",
            "2016-2020 arası",
            "2020-2024 arası"
        ]
        for i, option in enumerate(year_options[:3]):
            if row1[i].button(option, key=f"year_btn_{i}"):
                st.session_state.year_debt = option

        row2 = st.columns(3)
        for i, option in enumerate(year_options[3:], start=3):
            if row2[i-3].button(option, key=f"year_btn_{i}"):
                st.session_state.year_debt = option

        # Show the user's choice (if any)
        if st.session_state.year_debt:
            st.success(f"Seçtiğiniz: {st.session_state.year_debt}")
        else:
            st.info("Henüz bir yıl seçmediniz.")

        # "Devam" is disabled unless a choice has been made
        if st.button("Devam", disabled=(st.session_state.year_debt == ""), key="next0"):
            st.session_state.step = 1

    # ============= STEP 1 =============
    elif st.session_state.step == 1:
        st.subheader("B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?")
        # We'll do 4 radio buttons. The user must pick exactly one. If none is chosen, radio returns None.
        # If we want to preserve the old choice, set the 'index' accordingly or handle it manually.
        # But radio doesn't have a disabled option, so let's do a small hack:
        company_options = [
            "Mikro ölçekli işletme (1-9 çalışan)",
            "Küçük ölçekli işletme (10-49 çalışan)",
            "Orta ölçekli işletme (50-250 çalışan)",
            "Büyük ölçekli işletme (250 üzeri çalışan)"
        ]

        # If st.session_state.company_scale is in the list, find its index. Otherwise None => no selection.
        if st.session_state.company_scale in company_options:
            default_index = company_options.index(st.session_state.company_scale)
        else:
            default_index = -1  # means "no selection yet"

        # Build a radio widget with an extra "Seçiniz" label if default_index is -1
        # but we want to visually show no selection at first. We can do:
        chosen_scale = st.radio(
            "Seçiniz:",
            options=company_options,
            index=default_index if default_index >= 0 else 0,
            key="company_scale_radio"
        ) if default_index >= 0 else st.radio(
            "Seçiniz:",
            options=company_options,
            index=0,
            key="company_scale_radio"
        )

        # If default_index was -1, we forced index=0, which picks the first option. 
        # But we don't want that auto-chosen. So let's do a quick check:
        # We'll only update st.session_state.company_scale if the user changed it (Streamlit re-run).
        # We'll compare chosen_scale to the old value.
        if chosen_scale != st.session_state.company_scale:
            # That means the user just changed the radio selection
            st.session_state.company_scale = chosen_scale

        # If user hasn't changed from the default at all, we can interpret that as "no valid selection."
        # But radio doesn't easily let you have "no selection." We'll do a check:
        # If the user truly wants no selection yet, they'd have to forcibly do something. 
        # For a single-click approach, let's store the "initial" as empty. 
        # We'll do a small workaround below.

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back1"):
            st.session_state.step = 0

        # If the user didn't actually pick anything new, we treat it as empty:
        valid_choice = (st.session_state.company_scale in company_options)
        if col_next.button("Devam", disabled=(not valid_choice), key="next1"):
            st.session_state.step = 2

    # ============= STEP 2 =============
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

        if st.session_state.debt_amount in debt_options:
            default_index = debt_options.index(st.session_state.debt_amount)
        else:
            default_index = -1

        # Similar approach
        chosen_debt = st.radio(
            "Seçiniz:",
            debt_options,
            index=default_index if default_index >= 0 else 0,
            key="debt_amount_radio"
        ) if default_index >= 0 else st.radio(
            "Seçiniz:",
            debt_options,
            index=0,
            key="debt_amount_radio"
        )

        if chosen_debt != st.session_state.debt_amount:
            st.session_state.debt_amount = chosen_debt

        col_back, col_next = st.columns(2)
        if col_back.button("Geri", key="back2"):
            st.session_state.step = 1

        valid_choice = (st.session_state.debt_amount in debt_options)
        if col_next.button("Devam", disabled=(not valid_choice), key="next2"):
            st.session_state.step = 3

    # ============= STEP 3 =============
    elif st.session_state.step == 3:
        st.subheader("D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?")
        market_options = [
            "Sadece yurtiçi pazara hizmet veriyorum",
            "Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum",
            "Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum",
            "Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum",
            "Sadece yurtdışı pazara hizmet veriyorum"
        ]

        if st.session_state.market_served in market_options:
            default_index = market_options.index(st.session_state.market_served)
        else:
            default_index = -1

        chosen_market = st.radio(
            "Seçiniz:",
            market_options,
            index=default_index if default_index >= 0 else 0,
            key="market_served_radio"
        ) if default_index >= 0 else st.radio(
            "Seçiniz:",
            market_options,
            index=0,
            key="market_served_radio"
        )

        if chosen_market != st.session_state.market_served:
            st.session_state.market_served = chosen_market

        col_back, col_submit = st.columns(2)
        if col_back.button("Geri", key="back3"):
            st.session_state.step = 2

        valid_choice = (st.session_state.market_served in market_options)
        if col_submit.button("Gönder", disabled=(not valid_choice), key="submit_btn"):
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

# ---------------------------------
# Download Page
# ---------------------------------
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

# ---------------------------------
# Main App
# ---------------------------------
st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Seçiniz", ("Anket", "Sonuçları İndir"))
if page == "Anket":
    survey_page()
else:
    download_page()
