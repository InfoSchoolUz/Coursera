import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.title("📊 AI Leaders PINFL Checker (Online Report)")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=1)
    df.columns = df.columns.map(str).str.strip()

    st.success("✅ Fayl yuklandi")
    st.dataframe(df.head())

    # 🔥 USTUN TANLASH
    st.subheader("📌 Ustunlarni tanlang")

    col1, col2 = st.columns(2)

    with col1:
        region_col = st.selectbox("📍 Hudud (tuman)", df.columns)
        pinfl_col = st.selectbox("🆔 PINFL", df.columns)

    with col2:
        school_col = st.selectbox("🏫 Maktab", df.columns)

    if st.button("🚀 Tekshirishni boshlash"):

        progress = st.progress(0)
        status = st.empty()

        results = []

        total = len(df)

        for i, (_, row) in enumerate(df.iterrows()):
            pinfl = str(row[pinfl_col]).strip()

            try:
                res = requests.post(
                    "http://127.0.0.1:8000/check",
                    json={"pinfl": pinfl},
                    timeout=10
                ).json()

                # 🔥 sertifikat bor-yo‘qligi
                has_cert = 1 if str(res.get("courses", "0")) != "0" else 0

            except:
                has_cert = 0

            results.append(has_cert)

            progress.progress((i + 1) / total)
            status.text(f"🔄 Tekshirilmoqda: {i+1}/{total}")

        df["Sertifikat"] = results

        # 🔥 HISOBOT
        result = (
            df.groupby([region_col, school_col])
            .agg(
                Oquvchilar_soni=(pinfl_col, "count"),
                Sertifikat_olganlar=("Sertifikat", "sum")
            )
            .reset_index()
        )

        # 🔥 FOIZ
        result["%"] = (
            result["Sertifikat_olganlar"] /
            result["Oquvchilar_soni"].replace(0, 1) * 100
        ).round(2)

        # 🔥 FORMAT (sen xohlagan ko‘rinish)
        result.columns = [
            "Hudud",
            "Maktab raqami",
            "Maktabdagi o'quvchilar soni",
            "Sertifikat olganlar soni",
            "%"
        ]

        st.success("✅ Hisobot tayyor!")
        st.dataframe(result)

        # 🔥 Excel yuklab olish
        output = BytesIO()
        result.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "📥 Hisobotni yuklab olish",
            data=output,
            file_name="hisobot.xlsx"
        )
