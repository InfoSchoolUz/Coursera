import streamlit as st
import pandas as pd

st.title("📊 AI Leaders PINFL Checker (Offline)")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ustunlarni tozalash (bo'sh joylarni olib tashlash)
    df.columns = df.columns.str.strip()

    if "PINFL" not in df.columns:
        st.error("❌ 'PINFL' ustuni topilmadi!")
    else:
        pinfl_input = st.text_input("🔍 PINFL kiriting")

        if st.button("Tekshirish"):

            user = df[df["PINFL"].astype(str) == pinfl_input]

            if user.empty:
                st.error("❌ Topilmadi")
            else:
                row = user.iloc[0]

                # Email olish (agar mavjud bo‘lsa)
                email = row.get("Email", "Topilmadi")

                # 🔥 KURSLARNI ANIQLASH
                # kurs ustunlarini avtomatik topadi
                course_cols = [col for col in df.columns if "kurs" in col.lower()]

                total_courses = 0

                for col in course_cols:
                    value = row[col]
                    if pd.notna(value) and str(value).strip() != "":
                        total_courses += 1

                # 🎯 NATIJA
                st.success("✅ Topildi")

                st.markdown(f"""
                **📧 Email:** {email}  
                **🆔 PINFL:** {pinfl_input}  
                **📚 Topilgan kurslar:** {total_courses}
                """)

                if total_courses == 0:
                    st.info("ℹ️ Kurslar topilmadi")
