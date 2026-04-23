import streamlit as st
import pandas as pd
import time
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="PINFL Checker", layout="wide")

st.title("📊 Sertifikatlarni tekshirish (AI Leaders)")

uploaded_file = st.file_uploader("📂 Excel fayl yuklang", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.write("📋 Yuklangan ma'lumot:")
    st.dataframe(df.head())

    if "PINFL" not in df.columns:
        st.error("❌ Excelda 'PINFL' ustuni bo‘lishi kerak!")
    else:
        if st.button("🚀 Tekshirishni boshlash"):
            results = []

            progress = st.progress(0)
            status_text = st.empty()

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto("https://aileaders.uz/auth/login/check")

                total = len(df)

                for i, pinfl in enumerate(df["PINFL"]):
                    pinfl = str(pinfl)

                    status_text.text(f"🔍 Tekshirilmoqda: {pinfl}")

                    try:
                        # input tozalash
                        page.fill('input[placeholder="123123123"]', pinfl)

                        # tugma bosish
                        page.click("text=Tekshirish")

                        time.sleep(2)

                        # NATIJA BLOKNI OLISH
                        if page.locator("text=Topilgan kurslar").count() > 0:
                            result_text = page.locator("text=Topilgan kurslar").first.inner_text()
                        else:
                            result_text = "Topilmadi"

                    except Exception as e:
                        result_text = "Xatolik"

                    results.append({
                        "PINFL": pinfl,
                        "Natija": result_text
                    })

                    progress.progress((i + 1) / total)
                    time.sleep(2)

                browser.close()

            result_df = pd.DataFrame(results)

            st.success("✅ Tugadi!")
            st.dataframe(result_df)

            # download
            st.download_button(
                label="📥 Natijani yuklab olish",
                data=result_df.to_csv(index=False).encode('utf-8'),
                file_name="natija.csv",
                mime="text/csv"
            )
