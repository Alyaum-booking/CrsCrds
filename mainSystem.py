import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

# --- ملفات البيانات ---
DATA_FILE = "cards.xlsx"
OUTPUT_FILE = "powerbi_data.xlsx"
CARD_INFO_FILE = "CDB.xlsx"

plt.rcParams["font.family"] = "Tahoma"

# --- دعم العربية ---
def ar(text):
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# --- تشفير كلمة المرور ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- قاعدة بيانات المستخدمين ---
database = {
    "balyaqub": hash_password("Alyaum@123"),
    "aalomari": hash_password("Svmg#152")
}

# --- Session State للإبقاء على حالة تسجيل الدخول ---
if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 3
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.title("نظام تسجيل الدخول الآمن 🔐")

# --- تسجيل الدخول ---
if not st.session_state.logged_in:
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("دخول"):
        hashed = hash_password(password)
        if username in database and database[username] == hashed:
            st.success("تم تسجيل الدخول بنجاح ✅")
            st.session_state.logged_in = True
            st.rerun()  # ✅ الإصدار الجديد
        else:
            st.session_state.login_attempts -= 1
            st.error(f"بيانات خاطئة ❌ | المتبقي: {st.session_state.login_attempts} محاولة")
            if st.session_state.login_attempts <= 0:
                st.warning("تم قفل النظام 🔒")
                st.stop()

# --- بعد تسجيل الدخول ---
if st.session_state.logged_in:
    st.success("مرحبا بك في النظام ✅")

    # --- التحقق من الملفات ---
    for file_path in [DATA_FILE, CARD_INFO_FILE]:
        if not os.path.exists(file_path):
            st.error(f"{file_path} غير موجود ❌")
            st.stop()

    # --- قراءة بيانات البطاقات ---
    df_cards = pd.read_excel(DATA_FILE)

    # --- تجهيز البيانات ---
    data = {}
    for _, row in df_cards.iterrows():
        letter = str(row["letter"])
        number = str(row["number"])
        data.setdefault(letter, []).append(number)
    for letter in data:
        data[letter] = sorted(list(set(data[letter])))

    # --- اختيار المستخدم ---
    letter_selected = st.selectbox("اختر حرف البطاقة", options=list(data.keys()))
    number_selected = st.selectbox("اختر رقم البطاقة", options=data.get(letter_selected, []))

    if st.button("عرض لوحة معلومات البطاقة"):

        # --- قراءة ملف التحليل ---
        df_info = pd.read_excel(CARD_INFO_FILE)
        df_info["number"] = pd.to_numeric(df_info["number"], errors="coerce")
        number_selected_int = pd.to_numeric(number_selected, errors="coerce")

        card_data = df_info[
            (df_info["letter"] == letter_selected) &
            (df_info["number"] == number_selected_int)
        ]

        if card_data.empty:
            st.warning("البطاقة غير موجودة ⚠️")
        else:
            st.subheader("لوحة معلومات البطاقة")

            # --- تحضير البطاقات ---
            cards = []
            count = len(card_data)
            cards.append(("عدد السيارات", "حسب القيمة المختارة", count))

            for dept, val in card_data["endins"].value_counts().items():
                cards.append(("نهاية الفحص", dept, val))
            for stt, val in card_data["costins"].value_counts().items():
                cards.append(("تكلفة الفحص", stt, val))
            for stt, val in card_data["status"].value_counts().items():
                cards.append(("الحالة", stt, val))
            for stt, val in card_data["insstate"].value_counts().items():
                cards.append(("حالة الفحص", stt, val))
            for stt, val in card_data["dep"].value_counts().items():
                cards.append(("القسم", stt, val))
            for stt, val in card_data["feeofnewlen"].value_counts().items():
                cards.append(("رسوم تجديد الاستمارة", stt, val))
            for stt, val in card_data["fineofnolen"].value_counts().items():
                cards.append(("غرامة عدم تجديد الاستمارة", stt, val))
            for stt, val in card_data["driver"].value_counts().items():
                cards.append(("اسم السائق", stt, val))
            for stt, val in card_data["endlin"].value_counts().items():
                cards.append(("تاريخ انتهاء الاستمارة", stt, val))
            for stt, val in card_data["brand"].value_counts().items():
                cards.append(("الماركة", stt, val))
            for stt, val in card_data["carname"].value_counts().items():
                cards.append(("الطراز", stt, val))

            # --- رسم البطاقات باستخدام matplotlib ---
            plt.figure(figsize=(10, 5))
            plt.axis("off")

            cols = 3
            card_w = 1 / cols
            card_h = 0.25

            for i, (title, name, value) in enumerate(cards):
                row = i // cols
                col = i % cols
                x = col * card_w
                y = 1 - (row + 1) * card_h

                rect = plt.Rectangle(
                    (x, y),
                    card_w - 0.01,
                    card_h - 0.01,
                    edgecolor="black",
                    facecolor="lightblue"
                )
                plt.gca().add_patch(rect)

                plt.text(
                    x + 0.02,
                    y + card_h - 0.08,
                    ar(title),
                    fontsize=10,
                    weight="bold"
                )
                plt.text(
                    x + 0.02,
                    y + card_h - 0.15,
                    ar(name),
                    fontsize=9
                )
                plt.text(
                    x + 0.02,
                    y + 0.05,
                    str(value),
                    fontsize=14
                )

            plt.title(ar("لوحة معلومات البطاقة"))
            st.pyplot(plt)
