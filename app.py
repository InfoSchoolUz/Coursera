import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.title("📊 AI Leaders PINFL Checker (Online)")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "PINFL" not in df.columns:
        st.error("❌ PINFL ustuni yo‘q")
    else:
        if st.button("🚀 Tekshirishni boshlash"):

            results = []
            progress = st.progress(0)

            total = len(df)

            for i, pinfl in enumerate(df["PINFL"]):
                pinfl = str(pinfl)

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

            result_df = pd.DataFrame(results)
            st.dataframe(result_df)

            # Excel yuklab olish
            output = BytesIO()
            result_df.to_excel(output, index=False)
            output.seek(0)

            st.download_button(
                "📥 Excel yuklab olish",
                output,
                "natija.xlsx"
            )
