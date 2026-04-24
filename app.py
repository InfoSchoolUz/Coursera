import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.title("📊 AI Leaders PINFL Checker (Online)")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.map(str).str.strip()

    st.success("✅ Fayl yuklandi")
    st.dataframe(df.head())

    selected_col = st.selectbox("📌 PINFL ustunini tanlang", df.columns)

    if st.button("🚀 Tekshirishni boshlash"):

        results = []
        progress = st.progress(0)
        status_text = st.empty()

        total = len(df)

        for i, (_, row) in enumerate(df.iterrows()):
            pinfl = str(row[selected_col]).strip()

            try:
                res = requests.post(
                    "http://127.0.0.1:8000/check",
                    json={"pinfl": pinfl}
                ).json()

                results.append({
                    "PINFL": pinfl,
                    "Email": res["email"],
                    "Kurslar": res["courses"]
                })

            except:
                results.append({
                    "PINFL": pinfl,
                    "Email": "Xatolik",
                    "Kurslar": "Xatolik"
                })

            progress.progress((i + 1) / total)
            status_text.text(f"🔄 {i+1}/{total}")

        result_df = pd.DataFrame(results)

        st.success("✅ Tugadi!")
        st.dataframe(result_df)

        output = BytesIO()
        result_df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "📥 Excel yuklab olish",
            output,
            "natija.xlsx"
        )
