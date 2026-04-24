import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 AI Leaders PINFL Checker")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    st.success("✅ Fayl yuklandi")

    # 🔥 LIST TANLASH
    sheet_name = st.selectbox("📄 List (Sheet) tanlang", xls.sheet_names)

    # 🔥 HEADER MUAMMOSI UCHUN (2-qator header)
    df = pd.read_excel(xls, sheet_name=sheet_name, header=1)

    df.columns = df.columns.map(str).str.strip()

    st.dataframe(df.head())

    # 🔥 TUGMA
    if st.button("🚀 Tekshirishni boshlash"):

        progress = st.progress(0)
        status = st.empty()

        total_rows = len(df)

        for i in range(total_rows):
            progress.progress((i + 1) / total_rows)
            status.text(f"🔄 Hisoblanmoqda: {i+1}/{total_rows}")

        # 🔥 USTUNLARNI TO‘G‘RI TANLASH
        try:
            region_col = df.columns[0]
            school_col = df.columns[1]
            total_col = df.columns[2]
            success_col = df.columns[3]
        except:
            st.error("❌ Ustunlar yetarli emas")
            st.stop()

        result = df[[region_col, school_col, total_col, success_col]].copy()

        # 🔥 MUHIM FIX (string → number)
        result[total_col] = pd.to_numeric(result[total_col], errors="coerce").fillna(0)
        result[success_col] = pd.to_numeric(result[success_col], errors="coerce").fillna(0)

        # 🔥 FOIZ (0 ga bo‘linishdan himoya)
        result["%"] = (
            result[success_col] / result[total_col].replace(0, 1) * 100
        ).round(2)

        # 🔥 USTUN NOMLARI
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
