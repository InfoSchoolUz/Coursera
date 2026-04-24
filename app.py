import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 AI Leaders PINFL Checker (Offline Report)")

uploaded_file = st.file_uploader("📂 Excel yuklang", type=["xlsx"])

def find_pinfl_column(df):
    # ustunlarni tozalash
    df.columns = df.columns.str.strip()
    for col in df.columns:
        name = col.lower().strip()
        if name in ["pinfl", "пинфл"]:
            return col
    return None

def count_courses(row, df):
    course_cols = [c for c in df.columns if "kurs" in c.lower()]
    total = 0
    for c in course_cols:
        if pd.notna(row[c]) and str(row[c]).strip() != "":
            total += 1
    return total

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success("✅ Fayl yuklandi")
    st.dataframe(df.head())

    pinfl_col = find_pinfl_column(df)

    if not pinfl_col:
        st.error("❌ PINFL ustuni topilmadi (PINFL yoki ПИНФЛ)")
    else:
        if st.button("🚀 Tekshirishni boshlash"):

            result_courses = []
            result_status = []

            progress = st.progress(0)

            for i, (_, row) in enumerate(df.iterrows()):
                total_courses = count_courses(row, df)

                result_courses.append(total_courses)

                if total_courses > 0:
                    result_status.append("Topildi")
                else:
                    result_status.append("Topilmadi")

                progress.progress((i + 1) / len(df))

            # 🔥 YANGI USTUNLAR
            df["Kurslar_soni"] = result_courses
            df["Status"] = result_status

            st.success("✅ Tekshiruv tugadi!")
            st.dataframe(df)

            # 🔥 XLSX EXPORT
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.download_button(
                label="📥 Excel yuklab olish",
                data=output,
                file_name="hisobot.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
