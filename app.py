"""
AI Leaders PINFL Checker
========================
O'rnatish:
    pip install streamlit openpyxl pandas requests browser-cookie3

Ishga tushirish:
    streamlit run pinfl_checker.py

MUHIM: Ishga tushirishdan oldin Chrome da aileaders.uz ni oching
       va biror PINFL tekshiring (cookie yangilansin).
"""

import time
import requests
import browser_cookie3
import pandas as pd
import streamlit as st
from io import BytesIO

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
API_URL     = "https://aileaders.uz/api/v1/check/certificates"
DELAY_SEC   = 0.6
SKIP_SHEETS = {"ЖАМИ СЕРТИФИКАТ ОЛГАНЛАР", "Лист1"}

# ──────────────────────────────────────────
# CHROME DAN COOKIE OLISH
# ──────────────────────────────────────────
def get_cookies() -> dict:
    try:
        jar = browser_cookie3.chrome(domain_name="aileaders.uz")
        cookies = {c.name: c.value for c in jar}
        return cookies
    except Exception as e:
        return {"error": str(e)}

# ──────────────────────────────────────────
# EXCEL O'QISH
# ──────────────────────────────────────────
def read_excel(file) -> pd.DataFrame:
    xls = pd.ExcelFile(file, engine="openpyxl")
    frames = []

    for sheet in xls.sheet_names:
        if sheet in SKIP_SHEETS:
            continue
        try:
            df = pd.read_excel(xls, sheet_name=sheet, header=1, engine="openpyxl")
        except Exception:
            continue

        df.columns = df.columns.map(str).str.strip()

        pinfl_col = next((c for c in df.columns if "ПИНФЛ" in c or "PINFL" in c.upper()), None)
        name_col  = next((c for c in df.columns if "наименование" in c.lower()), None)

        if pinfl_col is None:
            continue

        cols = [c for c in [name_col, pinfl_col] if c]
        sub  = df[cols].copy()
        sub  = sub.rename(columns={pinfl_col: "PINFL", name_col: "F.I.Sh."})

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
    empty = {"holat": "", "ism": "", "email": "", "kurslar": 0, "yakunlangan": 0, "xato": ""}
    try:
        r = session.get(API_URL, params={"pinfl": pinfl}, timeout=15)

        if r.status_code in (200, 304):
            try:
                data = r.json()
            except Exception:
                return {**empty, "holat": "⚠️ JSON xato", "xato": r.text[:80]}

            courses     = data.get("courses", [])
            completed   = sum(1 for c in courses if c.get("isCompleted"))
            has_courses = data.get("hasCourses", False)

            return {
                "holat":       "✅ Sertifikat bor" if has_courses else "⚠️ Ro'yxatda bor, kurs yo'q",
                "ism":         data.get("fullName", ""),
                "email":       data.get("email", ""),
                "kurslar":     len(courses),
                "yakunlangan": completed,
                "xato":        "",
            }

        elif r.status_code == 404:
            return {**empty, "holat": "❌ Topilmadi"}
        elif r.status_code == 401:
            return {**empty, "holat": "🔐 Cookie eskirgan", "xato": "Cookie yangilang"}
        elif r.status_code == 429:
            time.sleep(15)
            return {**empty, "holat": "⏳ Rate limit", "xato": "Keyingi PINFL dan davom eting"}
        else:
            return {**empty, "holat": f"🔴 {r.status_code}", "xato": r.text[:80]}

    except Exception as e:
        return {**empty, "holat": "🔴 Xato", "xato": str(e)[:80]}

# ──────────────────────────────────────────
# STREAMLIT UI
# ──────────────────────────────────────────
st.set_page_config(page_title="AI Leaders PINFL Checker", page_icon="🎓", layout="wide")

st.title("🎓 AI Leaders — PINFL Sertifikat Tekshiruvi")
st.caption("Excel fayldagi barcha PINFLlarni aileaders.uz da avtomatik tekshiradi")

# ── 1-QADAM: COOKIE ──
st.subheader("🔐 1-qadam: Cookie olish")
st.info("Chrome da **aileaders.uz** oching, biror PINFL tekshiring, keyin quyidagi tugmani bosing.")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 Cookie olish", type="primary"):
        with st.spinner("Chrome dan cookie o'qilmoqda..."):
            cookies = get_cookies()

        if "error" in cookies:
            st.session_state.update({"cookie_status": "error", "cookies": {}, "cookie_msg": cookies["error"]})
        elif "HWWAFSESID" in cookies:
            st.session_state.update({"cookie_status": "ok", "cookies": cookies,
                                     "cookie_msg": f"HWWAFSESID: {cookies['HWWAFSESID'][:16]}..."})
        else:
            st.session_state.update({"cookie_status": "missing", "cookies": {},
                                     "cookie_msg": "Cookie topilmadi — Chrome da aileaders.uz ni oching!"})

with col2:
    status = st.session_state.get("cookie_status", "")
    if status == "ok":
        st.success(f"✅ Cookie muvaffaqiyatli olindi! `{st.session_state['cookie_msg']}`")
    elif status == "error":
        st.error(f"❌ Xato: {st.session_state['cookie_msg']}")
    elif status == "missing":
        st.warning(f"⚠️ {st.session_state['cookie_msg']}")

st.divider()

# ── 2-QADAM: EXCEL ──
st.subheader("📂 2-qadam: Excel yuklash")
uploaded = st.file_uploader("Excel faylni yuklang", type=["xlsx"], label_visibility="collapsed")

if uploaded:
    with st.spinner("Excel o'qilmoqda..."):
        df_all = read_excel(uploaded)

    if df_all.empty:
        st.error("❌ Excel dan PINFL topilmadi!")
        st.stop()

    st.success(f"✅ **{len(df_all)}** ta o'quvchi | **{df_all['Maktab'].nunique()}** ta maktab topildi")

    with st.expander("🏫 Maktab filtri (ixtiyoriy)"):
        maktablar = sorted(df_all["Maktab"].unique().tolist())
        tanlangan = st.multiselect("Tekshiriladigan maktablar (bo'sh = hammasi)", maktablar)
        if tanlangan:
            df_all = df_all[df_all["Maktab"].isin(tanlangan)]
            st.info(f"Tanlangan: {len(df_all)} ta o'quvchi")

    st.divider()

    # ── 3-QADAM: TEKSHIRISH ──
    st.subheader("🚀 3-qadam: Tekshirishni boshlash")

    cookie_ok = st.session_state.get("cookie_status") == "ok"
    if not cookie_ok:
        st.warning("⚠️ Avval 1-qadamda Cookie oling!")

    if cookie_ok and st.button("🚀 Tekshirishni boshlash", type="primary"):

        session = requests.Session()
        session.cookies.update(st.session_state["cookies"])
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept":     "*/*",
            "Referer":    "https://aileaders.uz/auth/login/check",
        })

        progress_bar = st.progress(0)
        status_text  = st.empty()
        results      = []
        total        = len(df_all)

        for i, row in enumerate(df_all.itertuples(), 1):
            pinfl = str(row.PINFL)
            status_text.text(f"🔄 {i}/{total} — PINFL: {pinfl} | {row.Maktab}")
            progress_bar.progress(i / total)

            res = check_pinfl(pinfl, session)

            if res["holat"] == "🔐 Cookie eskirgan":
                st.error("🔐 Cookie eskirdi! 1-qadamdan qayta boshlang.")
                break

            # F.I.Sh. ustunini xavfsiz olish
            fio = ""
            for attr in ["F_I_Sh_", "FISh", "F.I.Sh."]:
                fio = getattr(row, attr, "") or ""
                if fio:
                    break

            results.append({
                "Maktab":      row.Maktab,
                "F.I.Sh.":    fio,
                "PINFL":       pinfl,
                "Holat":       res["holat"],
                "Ism (sayt)":  res["ism"],
                "Email":       res["email"],
                "Kurslar":     res["kurslar"],
                "Yakunlangan": res["yakunlangan"],
                "Xato":        res["xato"],
            })
            time.sleep(DELAY_SEC)

        status_text.success(f"✅ Yakunlandi! {len(results)}/{total} ta tekshirildi")
        progress_bar.progress(1.0)

        if not results:
            st.stop()

        result_df = pd.DataFrame(results)

        # Statistika
        st.subheader("📊 Natijalar")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jami",           len(result_df))
        c2.metric("✅ Sertifikat",  (result_df["Holat"] == "✅ Sertifikat bor").sum())
        c3.metric("⚠️ Kurs yo'q",  (result_df["Holat"].str.contains("Ro'yxatda", na=False)).sum())
        c4.metric("❌ Topilmadi",   (result_df["Holat"] == "❌ Topilmadi").sum())

        st.dataframe(result_df, use_container_width=True)

        # Maktab xulosasi
        st.subheader("🏫 Maktab bo'yicha hisobot")
        summary = (
            result_df.groupby("Maktab")
            .agg(
                Jami=("PINFL", "count"),
                Sertifikat=("Holat", lambda x: (x == "✅ Sertifikat bor").sum()),
            )
            .assign(Foiz=lambda d: (d["Sertifikat"] / d["Jami"] * 100).round(1))
            .sort_values("Foiz", ascending=False)
            .reset_index()
        )
        st.dataframe(summary, use_container_width=True)

        # Excel yuklab olish
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            result_df.to_excel(writer, sheet_name="Natijalar",       index=False)
            summary.to_excel(  writer, sheet_name="Maktab xulosasi", index=False)
        out.seek(0)

        st.download_button(
            "📥 Hisobotni yuklab olish (Excel)",
            data=out,
            file_name="aileaders_hisobot.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
