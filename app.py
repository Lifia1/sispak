import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from hasil_perhitungan import compute_results

st.set_page_config(page_title="Sistem Pakar Fuzzy", layout="wide")

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR / "dataset_kandang.csv"

# session state
if "page" not in st.session_state:
    st.session_state["page"] = "input"
if "input_data" not in st.session_state:
    st.session_state["input_data"] = None
if "dataset" not in st.session_state:
    st.session_state["dataset"] = None

def go(page):
    st.session_state["page"] = page
    st.rerun()

# ---------------- LOAD DATASET AUTOMATIS ----------------
df_loaded = None

if CSV_PATH.exists():
    try:
        df_loaded = pd.read_csv(CSV_PATH)
        st.sidebar.success(f"Dataset lokal ditemukan: {CSV_PATH.name}")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca dataset lokal: {e}")

uploaded = st.sidebar.file_uploader("Upload CSV (opsional)", type=["csv"])
if uploaded:
    df_loaded = pd.read_csv(uploaded)
    st.sidebar.success("Menggunakan CSV hasil upload.")

st.session_state["dataset"] = df_loaded


# ---------------- SARAN PAKAR ----------------
def generate_saran(kd, dp, kategori):
    s = ""

    # ==================== ANALISIS KEPADATAN ====================
    if kd < 8:
        s += "- Kepadatan **rendah**. Ruang gerak ayam sangat baik dan risiko stres rendah.\n"
    elif kd <= 12:
        s += "- Kepadatan **sedang**. Masih aman, namun ventilasi dan litter perlu dijaga.\n"
    else:
        s += "- Kepadatan **tinggi**. Risiko heat stress dan peningkatan amonia cukup besar.\n"

    # ==================== ANALISIS DEPLESI ====================
    if dp < 5:
        s += "- Deplesi **rendah**, kondisi kesehatan dan manajemen kandang sangat baik.\n"
    elif dp <= 10:
        s += "- Deplesi **sedang**, perlu evaluasi nutrisi, ventilasi, dan pemerataan pakan.\n"
    else:
        s += "- Deplesi **tinggi**, mengindikasikan potensi penyakit atau manajemen yang tidak optimal.\n"

    # ==================== KESIMPULAN (lebih panjang) ====================
    if kategori == "Layak":
        s += (
            "\n**Kesimpulan:** Kandang berada dalam kondisi **layak** untuk pemeliharaan. "
            "Parameter kepadatan dan kesehatan ayam menunjukkan lingkungan yang stabil dan aman. "
            "Meskipun demikian, pengawasan rutin tetap diperlukan untuk menjaga performa, terutama "
            "pada aspek ventilasi, kebersihan litter, dan distribusi pakan agar kondisi ideal dapat terus dipertahankan."
        )

    elif kategori == "Kurang Layak":
        s += (
            "\n**Kesimpulan:** Kandang dinilai **kurang layak**. Beberapa parameter belum optimal dan dapat "
            "mempengaruhi kenyamanan ayam jika tidak segera diperbaiki. Perlu dilakukan penataan ulang ventilasi, "
            "pengaturan distribusi pakan, serta pengawasan suhu agar tekanan lingkungan dapat dikurangi. "
            "Perbaikan ini penting untuk mencegah penurunan performa dan meningkatnya deplesi."
        )

    else:
        s += (
            "\n**Kesimpulan:** Kandang berada dalam kategori **tidak layak**. Kondisi kepadatan dan tingkat deplesi "
            "menunjukkan adanya tekanan lingkungan yang signifikan. Tindakan cepat diperlukan, seperti mengurangi "
            "populasi, meningkatkan ventilasi, serta melakukan pemeriksaan kesehatan ayam secara menyeluruh. "
            "Jika langkah korektif tidak segera dilakukan, risiko kerugian produksi dan peningkatan kematian ayam "
            "akan semakin besar dalam waktu dekat."
        )

    return s


# ---------------- PAGE INPUT ----------------
if st.session_state["page"] == "input":
    st.title("Sistem Pakar Fuzzy Tsukamoto – Kelayakan Kandang Ayam")

    st.markdown("""
    ### 📋 Input Data Kandang
    Masukkan data kandang Anda untuk menilai kelayakan berdasarkan kepadatan dan deplesi.
    """)

    col1, col2 = st.columns(2)
    
    with col1:
        luas = st.number_input(
            "Luas Kandang (m²)", 
            min_value=1.0, 
            value=300.0,
            help="Luas total kandang dalam meter persegi"
        )
        
        jumlah = st.number_input(
            "Jumlah Ayam Awal", 
            min_value=1, 
            value=5000,
            help="Jumlah ayam saat awal periode pemeliharaan"
        )
    
    with col2:
        sisa = st.number_input(
            "Sisa Hidup Ayam", 
            min_value=0, 
            value=4800,
            help="Jumlah ayam yang masih hidup saat ini"
        )
        
        # Preview perhitungan
        if jumlah > 0:
            preview_kepadatan = jumlah / luas
            preview_deplesi = ((jumlah - sisa) / jumlah) * 100 if sisa <= jumlah else 0
            
            st.info(f"**Preview:**\n\n"
                   f"🐔 Kepadatan: {preview_kepadatan:.2f} ekor/m²\n\n"
                   f"💀 Deplesi: {preview_deplesi:.2f}%")

    st.markdown("---")
    
    # Tombol hitung
    if st.button("🔍 Hitung Kelayakan", type="primary", use_container_width=True):
        
        # Validasi 1: Sisa hidup tidak boleh lebih besar dari jumlah awal
        if sisa > jumlah:
            st.error("❌ **Error:** Sisa hidup ayam tidak boleh lebih besar dari jumlah awal!")
            st.warning(f"Sisa Hidup: **{sisa:,}** > Jumlah Awal: **{jumlah:,}**")
            st.stop()
        
        # Validasi 2: Luas kandang harus realistis
        if luas < 50:
            st.warning("⚠️ **Peringatan:** Luas kandang sangat kecil (< 50 m²). Pastikan data sudah benar.")
        
        # Validasi 3: Kepadatan ekstrem
        kepadatan_check = jumlah / luas
        if kepadatan_check > 20:
            st.warning(f"⚠️ **Peringatan:** Kepadatan sangat tinggi ({kepadatan_check:.1f} ekor/m²). "
                      "Ini dapat membahayakan kesehatan ayam!")
        
        # Validasi 4: Deplesi sangat tinggi
        deplesi_check = ((jumlah - sisa) / jumlah) * 100
        if deplesi_check > 20:
            st.warning(f"⚠️ **Peringatan:** Deplesi sangat tinggi ({deplesi_check:.1f}%). "
                      "Segera lakukan tindakan korektif!")
        
        # Jika semua validasi lolos, simpan data dan pindah halaman
        st.session_state["input_data"] = {
            "luas": luas, 
            "jumlah": jumlah, 
            "sisa": sisa
        }
        go("hasil")

    st.stop()


# ---------------- PAGE HASIL ----------------
if st.session_state["page"] == "hasil":

    if st.session_state["input_data"] is None:
        st.warning("Belum ada input.")
        st.button("Kembali", on_click=lambda: go("input"))
        st.stop()

    x = st.session_state["input_data"]
    df = st.session_state["dataset"]

    out = compute_results(x["luas"], x["jumlah"], x["sisa"], df)

    st.title("Hasil Perhitungan Fuzzy")

    col1, col2, col3 = st.columns(3)
    col1.metric("Kepadatan", f"{out['kepadatan_user']:.2f} ekor/m²")
    col2.metric("Deplesi", f"{out['deplesi_user']:.2f}%")
    col3.metric("Nilai Fuzzy", f"{out['fuzzy_val']:.2f}")

    # kategori
    if out["kategori"] == "Layak":
        st.success(f"Kategori: {out['kategori']}")
    elif out["kategori"] == "Kurang Layak":
        st.warning(f"Kategori: {out['kategori']}")
    else:
        st.error(f"Kategori: {out['kategori']}")

    # Saran pakar
    st.markdown("### Saran Pakar")
    st.info(generate_saran(out["kepadatan_user"], out["deplesi_user"], out["kategori"]))

    st.markdown("---")

    # ---------------- PERBANDINGAN DATASET ----------------
    if out["dataset_present"]:
        st.header("Perbandingan dengan Dataset")

        s = out["summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TOTAL AYAM", f"{s['total_ayam']:,}")
        c2.metric("TOTAL MATI", f"{s['total_mati']:,}")
        c3.metric("TOTAL AFKIR", "-")
        c4.metric("RATA KEPADATAN", f"{s['rata_kepadatan']:.2f}")

        st.altair_chart(out["chart_kepadatan"], use_container_width=True)

        colL, colR = st.columns(2)
        colL.altair_chart(out["chart_kepadatan_dist"], use_container_width=True)
        colR.altair_chart(out["chart_deplesi_dist"], use_container_width=True)

        st.markdown("### Kandang Paling Mirip")
        st.dataframe(out["top_similar"])

    else:
        st.info("Dataset tidak ditemukan. Pastikan dataset_kandang.csv berada di folder yang sama dengan app.py.")

    st.markdown("---")
    if st.button("Kembali ke Input"):
        go("input")

