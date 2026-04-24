"""
AI Leaders PINFL Checker
========================
O'rnatish:
    pip install streamlit openpyxl pandas requests

Ishga tushirish:
    streamlit run pinfl_checker.py
"""

import time
import requests
import pandas as pd
import streamlit as st
from io import BytesIO

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
API_URL   = "https://aileaders.uz/api/v1/check/certificates"
DELAY_SEC = 0.5   # So'rovlar orasidagi pauza (rate limit: 20 req/min)

SKIP_SHEETS = {"ЖАМИ СЕРТИФИКАТ ОЛГАНЛАР", "Лист1"}

# ──────────────────────────────────────────
# EXCEL O'QISH
# ──────────────────────────────────────────
def read_excel(file) -> pd.DataFrame:
    xls = pd.ExcelFile(file, engine="openpyxl")
    frames = []

    for sheet in xls.sheet_names:
        if sheet in SKIP_SHEETS:
            continue
        df = pd.read_excel(xls, sheet_name=sheet, header=1, engine="openpyxl")
        df.columns = df.columns.map(str).str.strip()

        pinfl_col = next((c for c in df.columns if "ПИНФЛ" in c or "PINFL" in c.upper()), None)
        name_col  = next((c for c in df.columns if "наименование" in c.lower()), None)

        if pinfl_col is None:
            continue

        sub = df[[c for c in [name_col, pinfl_col] if c]].copy()
        sub = sub.rename(columns={pinfl_col: "PINFL", name_col: "F.I.Sh."})
        sub["PINFL"] = (
            sub["PINFL"].astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        sub = sub[sub["PINFL"].str.len() >= 10]
        sub["Maktab"] = sheet
        frames.append(sub)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# ──────────────────────────────────────────
# BITTA PINFL TEKSHIRISH
# ──────────────────────────────────────────
def check_pinfl(pinfl: str, session: requests.Session) -> dict:
    try:
        r = session.get(
            API_URL,
            params={"pinfl": pinfl},
            timeout=15,
        )

        if r.status_code in (200, 304):
            try:
                data = r.json()
            except Exception:
                return {"holat": "⚠️ JSON xato", "ism": "", "email": "", "kurslar": 0, "xato": r.text[:100]}

            has = data.get("hasCourses", False)
            courses = data.get("courses", [])
            completed = sum(1 for c in courses if c.get("isCompleted"))

            return {
                "holat":   "✅ Topildi" if has else "❌ Kurs yo'q",
                "ism":     data.get("fullName", ""),
                "email":   data.get("email", ""),
                "kurslar": len(courses),
                "yakunlangan": completed,
                "xato":    "",
            }

        elif r.status_code == 404:
            return {"holat": "❌ Topilmadi", "ism": "", "email": "", "kurslar": 0, "yakunlangan": 0, "xato": ""}
        elif r.status_code == 429:
            time.sleep(10)
            return {"holat": "⏳ Rate limit", "ism": "", "email": "", "kurslar": 0, "yakunlangan": 0, "xato": "Qayta urinib ko'ring"}
        else:
            return {"holat": f"🔴 {r.status_code}", "ism": "", "email": "", "kurslar": 0, "yakunlangan": 0, "xato": r.text[:100]}

    except Exception as e:
        return {"holat": "🔴 Xato", "ism": "", "email": "", "kurslar": 0, "yakunlangan": 0, "xato": str(e)[:100]}

# ──────────────────────────────────────────
# UI
# ──────────────────────────────────────────
st.set_page_config(
    page_title="AI Leaders PINFL Checker",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 AI Leaders — PINFL Sertifikat Tekshiruvi")
st.caption("Excel fayldagi barcha PINFLlarni aileaders.uz da avtomatik tekshiradi")

# ── Cookie kiriting ──
st.subheader("🔐 Cookie (brauzerdan oling)")
with st.expander("Cookie qanday olish kerak?", expanded=False):
    st.markdown("""
    1. **Chrome** da `https://aileaders.uz/auth/login/check` oching
    2. Biror PINFL kiritib **Tekshirish** bosing
    3. **F12** → **Network** → `certificates?pinfl=...` so'rovga bosing
    4. **Headers** → **Request Headers** → `Cookie` qatorini ko'chiring
    5. Quyidagi maydonga joylashtiring
    """)

cookie_input = st.text_area(
    "Cookie qiymatini joylashtiring",
    placeholder="HWWAFSESTIME=1776997658109; HWWAFSESID=21bc97676c2a2d057a",
    height=80,
)

st.divider()

# ── Excel yuklash ──
uploaded = st.file_uploader("📂 Excel faylni yuklang", type=["xlsx"])

if uploaded and cookie_input.strip():
    with st.spinner("📖 Excel o'qilmoqda..."):
        df_all = read_excel(uploaded)

    if df_all.empty:
        st.error("❌ Excel dan PINFL ustuni topilmadi!")
        st.stop()

    st.success(f"✅ Jami **{len(df_all)}** ta o'quvchi, **{df_all['Maktab'].nunique()}** ta maktab")

    # Maktab filtri
    maktablar = sorted(df_all["Maktab"].unique().tolist())
    tanlangan = st.multiselect(
        "🏫 Maktab tanlang (bo'sh = hammasi)",
        maktablar,
    )
    if tanlangan:
        df_all = df_all[df_all["Maktab"].isin(tanlangan)]

    st.info(f"📋 Tekshiriladigan: **{len(df_all)}** ta o'quvchi")

    if st.button("🚀 Tekshirishni boshlash", type="primary"):

        # Session sozlash
        session = requests.Session()
        session.headers.update({
            "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept":       "*/*",
            "Content-Type": "application/json",
            "Referer":      "https://aileaders.uz/auth/login/check",
            "Cookie":       cookie_input.strip(),
        })

        progress_bar = st.progress(0)
        status_text  = st.empty()
        results      = []
        total        = len(df_all)

        for i, row in enumerate(df_all.itertuples(), 1):
            status_text.text(f"🔄 {i}/{total} — {row.PINFL} | {row.Maktab}")
            progress_bar.progress(i / total)

            res = check_pinfl(str(row.PINFL), session)
            results.append({
                "Maktab":      row.Maktab,
                "F.I.Sh.":    getattr(row, "F.I.Sh.", ""),
                "PINFL":       row.PINFL,
                "Holat":       res["holat"],
                "Ism (sayt)":  res["ism"],
                "Email":       res["email"],
                "Kurslar":     res["kurslar"],
                "Yakunlangan": res.get("yakunlangan", 0),
                "Xato":        res["xato"],
            })
            time.sleep(DELAY_SEC)

        status_text.success("✅ Tekshiruv yakunlandi!")
        progress_bar.progress(1.0)

        result_df = pd.DataFrame(results)

        # ── Statistika ──
        st.subheader("📊 Umumiy natija")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jami",        len(result_df))
        c2.metric("✅ Topildi",  (result_df["Holat"] == "✅ Topildi").sum())
        c3.metric("❌ Kurs yo'q",(result_df["Holat"] == "❌ Kurs yo'q").sum())
        c4.metric("❌ Topilmadi",(result_df["Holat"] == "❌ Topilmadi").sum())

        st.dataframe(result_df, use_container_width=True)

        # ── Maktab xulosasi ──
        st.subheader("🏫 Maktab bo'yicha hisobot")
        summary = (
            result_df.groupby("Maktab")
            .agg(
                Jami=("PINFL", "count"),
                Topildi=("Holat", lambda x: (x == "✅ Topildi").sum()),
            )
            .assign(Foiz=lambda d: (d["Topildi"] / d["Jami"] * 100).round(1))
            .sort_values("Foiz", ascending=False)
            .reset_index()
        )
        st.dataframe(summary, use_container_width=True)

        # ── Excel export ──
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            result_df.to_excel(writer, sheet_name="Natijalar", index=False)
            summary.to_excel(writer, sheet_name="Maktab xulosasi", index=False)
        out.seek(0)

        st.download_button(
            "📥 Hisobotni yuklab olish (Excel)",
            data=out,
            file_name="aileaders_hisobot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

elif uploaded and not cookie_input.strip():
    st.warning("⚠️ Iltimos, avval Cookie ni kiriting!")
elif not uploaded and cookie_input.strip():
    st.warning("⚠️ Iltimos, Excel faylni yuklang!")
