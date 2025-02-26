import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
from io import BytesIO

# --- Database setup ---
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

def save_response(year_debt, company_scale, debt_amount, market_served):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO responses (year_debt, company_scale, debt_amount, market_served) VALUES (?, ?, ?, ?)",
              (year_debt, company_scale, debt_amount, market_served))
    conn.commit()
    conn.close()

def load_responses():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM responses", conn)
    conn.close()
    return df

# --- HTML Template (only change is the handleSubmit function) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Anket</title>
  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <style>
    .question-page { display: none; }
    .custom-radio {
      -webkit-appearance: none;
      -moz-appearance: none;
      appearance: none;
      width: 20px;
      height: 20px;
      border: 1px solid #adb5bd;
      border-radius: 0;
      outline: none;
      cursor: pointer;
      margin-right: 10px;
      position: relative;
    }
    .custom-radio:checked {
      background-color: #0d6efd;
      border-color: #0d6efd;
    }
  </style>
  <script>
    var currentQuestion = 0;
    var questions = ["question1", "question2", "question3", "question4"];
    function showQuestion(index) {
      questions.forEach(function(id, i) {
        document.getElementById(id).style.display = (i === index ? "block" : "none");
      });
      updateProgress();
    }
    function updateProgress() {
      var progress = ((currentQuestion + 1) / questions.length) * 100;
      document.getElementById("progressBar").style.width = progress + "%";
      document.getElementById("progressBar").innerText = Math.round(progress) + "%";
    }
    function enableButton(buttonId) {
      var btn = document.getElementById(buttonId);
      btn.disabled = false;
      btn.classList.remove("btn-secondary");
      btn.classList.add("btn-primary");
    }
    function disableButton(buttonId) {
      var btn = document.getElementById(buttonId);
      btn.disabled = true;
      btn.classList.remove("btn-primary");
      btn.classList.add("btn-secondary");
    }
    function selectYear(value) {
      document.getElementById("year_debt_input").value = value;
      var buttons = document.getElementsByClassName("year-button");
      for (var i = 0; i < buttons.length; i++){
        buttons[i].classList.remove("btn-primary");
        buttons[i].classList.add("btn-outline-primary");
      }
      document.getElementById(value).classList.remove("btn-outline-primary");
      document.getElementById(value).classList.add("btn-primary");
      enableButton("next1");
    }
    function selectDebtAmountRadio(radio) {
      document.getElementById("debt_amount_input").value = radio.value;
      enableButton("next3");
    }
    function validateSelect(selectId, buttonId) {
      var selectElement = document.getElementById(selectId);
      if (selectElement.value !== "") {
        enableButton(buttonId);
      } else {
        disableButton(buttonId);
      }
    }
    function nextQuestion() {
      if (currentQuestion < questions.length - 1) {
        currentQuestion++;
        showQuestion(currentQuestion);
      }
    }
    function prevQuestion() {
      if (currentQuestion > 0) {
        currentQuestion--;
        showQuestion(currentQuestion);
      }
    }
    window.onload = function() {
      showQuestion(0);
      disableButton("next1");
      disableButton("next2");
      disableButton("next3");
      disableButton("submitButton");
      updateProgress();
    }

    // Only change: we now build the redirect URL from window.location.href
    function handleSubmit(e) {
      e.preventDefault();
      var year_debt = document.getElementById("year_debt_input").value;
      var company_scale = document.getElementById("select_company_scale").value;
      var debt_amount = document.getElementById("debt_amount_input").value;
      var market_served = document.getElementById("select_market_served").value;

      // Remove any existing query string from the current URL:
      var baseUrl = window.location.href.split('?')[0];
      // Build the new URL with query parameters:
      var url = baseUrl
        + "?year_debt=" + encodeURIComponent(year_debt)
        + "&company_scale=" + encodeURIComponent(company_scale)
        + "&debt_amount=" + encodeURIComponent(debt_amount)
        + "&market_served=" + encodeURIComponent(market_served);
      window.location.href = url;
    }
  </script>
</head>
<body class="container mt-5">
  <h2 class="mb-4">Şirket Borç Durumu Anketi</h2>
  <!-- Progress Bar -->
  <div class="progress mb-4">
    <div class="progress-bar" role="progressbar" id="progressBar" style="width: 25%;" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100">25%</div>
  </div>
  <form id="surveyForm" onsubmit="handleSubmit(event)">
    <!-- Question 1 -->
    <div id="question1" class="question-page">
      <div class="mb-3">
        <label class="form-label"><b>A. Firmanızın en çok borçlandığı yıl hangisidir?</b></label>
        <div class="d-grid gap-2">
          <input type="hidden" name="year_debt" id="year_debt_input" required>
          <button type="button" id="2000 ve öncesi" class="btn btn-outline-primary year-button" onclick="selectYear('2000 ve öncesi')">2000 ve öncesi</button>
          <button type="button" id="2001-2005 arası" class="btn btn-outline-primary year-button" onclick="selectYear('2001-2005 arası')">2001-2005 arası</button>
          <button type="button" id="2006-2010 arası" class="btn btn-outline-primary year-button" onclick="selectYear('2006-2010 arası')">2006-2010 arası</button>
          <button type="button" id="2011-2015 arası" class="btn btn-outline-primary year-button" onclick="selectYear('2011-2015 arası')">2011-2015 arası</button>
          <button type="button" id="2016-2020 arası" class="btn btn-outline-primary year-button" onclick="selectYear('2016-2020 arası')">2016-2020 arası</button>
          <button type="button" id="2020-2024 arası" class="btn btn-outline-primary year-button" onclick="selectYear('2020-2024 arası')">2020-2024 arası</button>
        </div>
      </div>
      <div class="d-flex justify-content-end">
        <button type="button" id="next1" class="btn btn-secondary" onclick="nextQuestion()" disabled>Devam</button>
      </div>
    </div>

    <!-- Question 2 -->
    <div id="question2" class="question-page">
      <div class="mb-3">
        <label class="form-label"><b>B. Firmanızın borçlu olduğu işletme en çok hangi ölçektedir?</b></label>
        <select name="company_scale" id="select_company_scale" class="form-select" onchange="validateSelect('select_company_scale', 'next2')" required>
          <option value="">Seçiniz</option>
          <option value="Mikro ölçekli işletme (1-9 çalışan)">Mikro ölçekli işletme (1-9 çalışan)</option>
          <option value="Küçük ölçekli işletme (10-49 çalışan)">Küçük ölçekli işletme (10-49 çalışan)</option>
          <option value="Orta ölçekli işletme (50-250 çalışan)">Orta ölçekli işletme (50-250 çalışan)</option>
          <option value="Büyük ölçekli işletme (250 üzeri çalışan)">Büyük ölçekli işletme (250 üzeri çalışan)</option>
        </select>
      </div>
      <div class="d-flex justify-content-between">
        <button type="button" class="btn btn-primary" onclick="prevQuestion()">Geri</button>
        <button type="button" id="next2" class="btn btn-secondary" onclick="nextQuestion()" disabled>Devam</button>
      </div>
    </div>

    <!-- Question 3 -->
    <div id="question3" class="question-page">
      <div class="mb-3">
        <label class="form-label"><b>C. Firmanızın borç oranı nedir?</b></label>
        <input type="hidden" name="debt_amount" id="debt_amount_input" required>
        <div>
          <div class="form-check mb-2">
            <input class="form-check-input custom-radio" type="radio" name="debt_amount_radio" id="option1" value="0-1 milyon TL" onclick="selectDebtAmountRadio(this)">
            <label class="form-check-label" for="option1">0-1 milyon TL</label>
          </div>
          <div class="form-check mb-2">
            <input class="form-check-input custom-radio" type="radio" name="debt_amount_radio" id="option2" value="1-5 milyon TL" onclick="selectDebtAmountRadio(this)">
            <label class="form-check-label" for="option2">1-5 milyon TL</label>
          </div>
          <div class="form-check mb-2">
            <input class="form-check-input custom-radio" type="radio" name="debt_amount_radio" id="option3" value="5-10 milyon TL" onclick="selectDebtAmountRadio(this)">
            <label class="form-check-label" for="option3">5-10 milyon TL</label>
          </div>
          <div class="form-check mb-2">
            <input class="form-check-input custom-radio" type="radio" name="debt_amount_radio" id="option4" value="10-50 milyon TL" onclick="selectDebtAmountRadio(this)">
            <label class="form-check-label" for="option4">10-50 milyon TL</label>
          </div>
          <div class="form-check mb-2">
            <input class="form-check-input custom-radio" type="radio" name="debt_amount_radio" id="option5" value="50 milyon TL ve üzeri" onclick="selectDebtAmountRadio(this)">
            <label class="form-check-label" for="option5">50 milyon TL ve üzeri</label>
          </div>
          <div class="form-check mb-2">
            <input class="form-check-input custom-radio" type="radio" name="debt_amount_radio" id="option6" value="Belirtmek istemiyorum" onclick="selectDebtAmountRadio(this)">
            <label class="form-check-label" for="option6">Belirtmek istemiyorum</label>
          </div>
        </div>
      </div>
      <div class="d-flex justify-content-between">
        <button type="button" class="btn btn-primary" onclick="prevQuestion()">Geri</button>
        <button type="button" id="next3" class="btn btn-secondary" onclick="nextQuestion()" disabled>Devam</button>
      </div>
    </div>

    <!-- Question 4 -->
    <div id="question4" class="question-page">
      <div class="mb-3">
        <label class="form-label"><b>D. Firmanız ağırlıklı olarak hangi pazarlara hizmet veriyor?</b></label>
        <select name="market_served" id="select_market_served" class="form-select" onchange="validateSelect('select_market_served', 'submitButton')" required>
          <option value="" disabled selected hidden></option>
          <option value="Sadece yurtiçi pazara hizmet veriyorum">1. Sadece yurtiçi pazara hizmet veriyorum</option>
          <option value="Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum">2. Ağırlıklı olarak yurtiçi pazara, kısmen yurtdışı pazara hizmet veriyorum</option>
          <option value="Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum">3. Hem yurtiçi hem yurtdışı pazarlara eşit oranda hizmet veriyorum</option>
          <option value="Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum">4. Ağırlıklı olarak yurtdışı pazara, kısmen yurtiçi pazara hizmet veriyorum</option>
          <option value="Sadece yurtdışı pazara hizmet veriyorum">5. Sadece yurtdışı pazara hizmet veriyorum</option>
        </select>
      </div>
      <div class="d-flex justify-content-between">
        <button type="button" class="btn btn-primary" onclick="prevQuestion()">Geri</button>
        <button type="submit" id="submitButton" class="btn btn-secondary" disabled>Gönder</button>
      </div>
    </div>
  </form>
</body>
</html>
"""

# --- Streamlit app logic ---

# Remove the old st.experimental_get_query_params usage:
params_dict = st.query_params  # returns a dict of param -> list of strings

# If there's a ?page=download in the URL, show admin page
if "page" in params_dict and "download" in params_dict["page"]:
    st.title("Download Survey Results")
    st.write("Bu sayfa yalnızca yetkili kullanıcılar içindir.")
    admin_username = st.text_input("Kullanıcı Adı")
    admin_password = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if admin_username == "user.vision" and admin_password == "cemisthe.bestfreelancer.ever":
            df = load_responses()
            st.subheader("Kayıtlı Yanıtlar")
            st.dataframe(df)
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

# Otherwise, it's the main survey page
else:
    # So we don't re-save on every page load:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    # Extract each param (which is a list of strings). If missing, get an empty list.
    year_debt_list = params_dict.get("year_debt", [])
    company_scale_list = params_dict.get("company_scale", [])
    debt_amount_list = params_dict.get("debt_amount", [])
    market_served_list = params_dict.get("market_served", [])

    # If all parameters are present and we haven't already submitted:
    if (not st.session_state.submitted
        and len(year_debt_list) > 0
        and len(company_scale_list) > 0
        and len(debt_amount_list) > 0
        and len(market_served_list) > 0):
        
        # They are lists, so take the first item
        year_debt = year_debt_list[0]
        company_scale = company_scale_list[0]
        debt_amount = debt_amount_list[0]
        market_served = market_served_list[0]

        save_response(year_debt, company_scale, debt_amount, market_served)
        st.session_state.submitted = True
        st.success("Teşekkürler! Cevabınız kaydedildi.")
        st.markdown("[Ankete tekrar katılmak için tıklayın](./)")

    else:
        # Show your custom HTML form
        components.html(HTML_TEMPLATE, height=800, scrolling=True)
        # Optional link for admin
        st.markdown("[Download Results (Admin)](?page=download)")
