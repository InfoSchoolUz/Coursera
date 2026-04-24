import streamlit as st
import pandas as pd
import time
from playwright.sync_api import sync_playwright

st.title("📊 AI Leaders PINFL Checker")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "PINFL" not in df.columns:
        st.error("❌ 'PINFL' ustuni topilmadi!")
    else:
        if st.button("🚀 Tekshirishni boshlash"):

            results = []
            progress = st.progress(0)
            status = st.empty()

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto("https://aileaders.uz/auth/login/check")

                for i, pinfl in enumerate(df["PINFL"]):
                    pinfl = str(pinfl)

                    status.text(f"🔍 Tekshirilmoqda: {pinfl}")

                    try:
                        # INPUTLAR
                        inputs = page.locator("input")
                        inputs.nth(1).fill("")  # tozalash
                        inputs.nth(1).fill(pinfl)

                        # BUTTON
                        page.locator("button").filter(has_text="Tekshirish").click()

                        # NATIJA CHIQISHINI KUTISH
                        page.wait_for_timeout(2000)

                        # 🔥 ASOSIY QISM (YASHIL BLOKNI OLISH)
                        body = page.inner_text("body")

                        # DEFAULT
                        email = ""
                        courses = "0"

                        if "Email:" in body:
                            try:
                                email = body.split("Email:")[1].split("\n")[0].strip()
                            except:
                                email = "Topilmadi"

                        if "Topilgan kurslar:" in body:
                            try:
                                courses = body.split("Topilgan kurslar:")[1].split("\n")[0].strip()
                            except:
                                courses = "0"

                        results.append({
                            "PINFL": pinfl,
                            "Email": email,
                            "Kurslar_soni": courses
                        })

                    except Exception as e:
                        results.append({
                            "PINFL": pinfl,
                            "Email": "Xatolik",
                            "Kurslar_soni": "Xatolik"
                        })

                    progress.progress((i + 1) / len(df))
                    time.sleep(2)

                browser.close()

            result_df = pd.DataFrame(results)

            st.success("✅ Tugadi!")
            st.dataframe(result_df)

            st.download_button(
                "📥 CSV yuklab olish",
                result_df.to_csv(index=False).encode("utf-8"),
                "natija.csv"
            )
