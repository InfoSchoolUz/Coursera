import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 AI Leaders PINFL Checker (Online)")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

# 1️⃣ Fayl yuklandi → jim turadi
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.map(str).str.strip()

    st.success("✅ Fayl yuklandi")

    # 2️⃣ Sheet/ustun tanlash → jim turadi
    col1, col2 = st.columns(2)

    with col1:
        region_col = st.selectbox("📍 Viloyat / Tuman ustuni", df.columns)

    with col2:
        org_col = st.selectbox("🏫 Maktab (tashkilot) ustuni", df.columns)

    col3, col4 = st.columns(2)

    with col3:
        total_col = st.selectbox("👥 Jami son ustuni", df.columns)

    with col4:
        success_col = st.selectbox("🎓 Sertifikat olganlar ustuni", df.columns)

    # 3️⃣ Tugma chiqadi
    if st.button("🚀 Tekshirishni boshlash"):

        progress = st.progress(0)
        status = st.empty()

        total_rows = len(df)

        # progress (faqat animatsiya uchun)
        for i in range(total_rows):
            progress.progress((i + 1) / total_rows)
            status.text(f"🔄 Hisoblanmoqda: {i+1}/{total_rows}")

        # 4️⃣ HISOBOT (sen xohlagan format)
        result = (
            df.groupby([region_col, org_col], as_index=False)
            .agg({
                total_col: "sum",
                success_col: "sum"
            })
        )

        # foiz hisoblash
        result["%"] = (result[success_col] / result[total_col] * 100).round(2)

        # ustun nomlarini chiroyli qilish
        result.columns = [
            "Hudud",
            "Maktab",
            "Jami",
            "Sertifikat olganlar",
            "%"
        ]

        st.success("✅ Hisobot tayyor!")

        st.dataframe(result)

        # Excel export
        output = BytesIO()
        result.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "📥 Hisobotni yuklab olish",
            data=output,
            file_name="hisobot.xlsx"
        )
