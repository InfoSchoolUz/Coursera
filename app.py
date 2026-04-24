import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 AI Leaders PINFL Checker")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

# 1️⃣ Fayl yuklandi
if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    st.success("✅ Fayl yuklandi")

    # 🔥 2️⃣ LIST TANLASH (sheet)
    sheet_name = st.selectbox(
        "📄 List (Sheet) tanlang",
        xls.sheet_names
    )

    # hali hech narsa ishlamaydi
    df = pd.read_excel(xls, sheet_name=sheet_name)

    st.dataframe(df.head())

    # 🔥 3️⃣ TUGMA
    if st.button("🚀 Tekshirishni boshlash"):

        progress = st.progress(0)
        status = st.empty()

        total_rows = len(df)

        # progress animatsiya
        for i in range(total_rows):
            progress.progress((i + 1) / total_rows)
            status.text(f"🔄 Hisoblanmoqda: {i+1}/{total_rows}")

        # 🔥 4️⃣ HISOBOT (sen yuborgan rasmga o‘xshash)
        # bu yerda ustunlar index orqali olinadi
        try:
            region_col = df.columns[0]   # A
            school_col = df.columns[1]   # B
            total_col = df.columns[2]    # C
            success_col = df.columns[3]  # D
        except:
            st.error("❌ Ustunlar yetarli emas")
            st.stop()

        result = df[[region_col, school_col, total_col, success_col]].copy()

        # foiz hisoblash
        result["%"] = (result[success_col] / result[total_col] * 100).round(2)

        # rename
        result.columns = [
            "Hudud",
            "Maktab",
            "Jami",
            "Sertifikat olganlar",
            "%"
        ]

        st.success("✅ Hisobot tayyor!")
        st.dataframe(result)

        # 🔥 Excel export
        output = BytesIO()
        result.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "📥 Hisobotni yuklab olish",
            data=output,
            file_name="hisobot.xlsx"
        )
