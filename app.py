# app.py - FINAL VERSION
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from hasil_perhitungan import compute_results
from io import StringIO

st.set_page_config(page_title="Sistem Pakar Fuzzy", layout="wide")

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR / "dataset_kandang.csv"

# ============================================
# INISIALISASI SESSION STATE
# ============================================
if "page" not in st.session_state:
    st.session_state["page"] = "input"
if "input_data" not in st.session_state:
    st.session_state["input_data"] = None
if "dataset" not in st.session_state:
    st.session_state["dataset"] = None
if "dataset_source" not in st.session_state:
    st.session_state["dataset_source"] = None

def go(page):
    st.session_state["page"] = page
    st.rerun()


# ============================================
# FUNGSI LOAD CSV FLEXIBLE
# ============================================
def fix_single_line_csv(content):
    """
    Memperbaiki CSV yang semua datanya di satu baris
    """
    lines = content.strip().split('\n')
    
    if len(lines) <= 1:
        # Semua data di satu baris
        all_values = content.strip().split(',')
        
        # Deteksi header (cari nilai yang bukan angka)
        header_end = 0
        for i, val in enumerate(all_values):
            cleaned = val.strip().replace('.', '').replace('-', '')
            if cleaned and not cleaned.isdigit():
                header_end = i + 1
            else:
                if header_end > 0:
                    break
        
        if header_end == 0:
            # Coba asumsi 11 kolom (sesuai dataset standard)
            header_end = 11
        
        headers = all_values[:header_end]
        data_values = all_values[header_end:]
        
        # Pecah data per num_cols
        fixed_lines = [','.join(headers)]
        for i in range(0, len(data_values), header_end):
            row = data_values[i:i+header_end]
            if len(row) == header_end:
                fixed_lines.append(','.join(row))
        
        return '\n'.join(fixed_lines)
    
    # Jika sudah multi-line, cek apakah ada baris yang terlalu panjang
    header = lines[0].split(',')
    num_cols = len(header)
    
    fixed_lines = [lines[0]]
    for line in lines[1:]:
        values = line.split(',')
        if len(values) > num_cols:
            # Pecah baris ini
            for j in range(0, len(values), num_cols):
                row = values[j:j+num_cols]
                if len(row) == num_cols:
                    fixed_lines.append(','.join(row))
        elif len(values) == num_cols:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def load_csv_flexible(file_or_path):
    """
    Load CSV dengan berbagai format dan auto-fix jika rusak
    """
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    separators = [',', ';', '\t']
    
    # Baca raw content
    try:
        if isinstance(file_or_path, (str, Path)):
            with open(file_or_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()
        else:
            # File upload dari streamlit
            file_or_path.seek(0)
            raw_content = file_or_path.read()
            if isinstance(raw_content, bytes):
                raw_content = raw_content.decode('utf-8', errors='ignore')
    except Exception as e:
        st.error(f"Error membaca file: {e}")
        return None, None, None
    
    # Perbaiki jika rusak
    fixed_content = fix_single_line_csv(raw_content)
    
    # Coba parse
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(StringIO(fixed_content), sep=sep)
                
                # Validasi kolom
                required_cols = ['Jumlah_Ayam', 'Kepadatan']
                if all(col in df.columns for col in required_cols):
                    return df, encoding, sep
            except:
                continue
    
    return None, None, None


# ============================================
# SIDEBAR: DATASET MANAGEMENT
# ============================================
st.sidebar.title("📊 Dataset Management")
st.sidebar.markdown("---")

# Info penting untuk user
with st.sidebar.expander("ℹ️ Cara Upload Dataset", expanded=False):
    st.markdown("""
    **Format CSV yang diterima:**
    - Delimiter: koma (`,`)
    - Encoding: UTF-8
    - Kolom wajib: `Jumlah_Ayam`, `Kepadatan`, `Deplesi_pct`
    
    **Contoh format:**
    ```
    No,Kandang,Luas_m2,Jumlah_Ayam,Kepadatan,...
    1,5A,464.95,5220,11.23,...
    2,5B,428.7,4330,10.1,...
    ```
    
    **Tips:**
    - Pastikan setiap baris adalah satu data kandang
    - Hindari spasi di nama kolom
    - Simpan dengan encoding UTF-8
    """)

# Upload dataset
uploaded_file = st.sidebar.file_uploader(
    "📤 Upload Dataset CSV",
    type=['csv'],
    help="Upload file CSV dengan data kandang Anda",
    key="dataset_uploader"
)

# Process upload
if uploaded_file is not None:
    with st.sidebar:
        with st.spinner("🔄 Memproses dataset..."):
            df_uploaded, enc, sep = load_csv_flexible(uploaded_file)
            
            if df_uploaded is not None:
                # PENTING: Simpan ke session state SEGERA
                st.session_state["dataset"] = df_uploaded.copy()  # .copy() penting!
                st.session_state["dataset_source"] = "uploaded"
                
                st.success("✅ Dataset berhasil diupload!")
                st.info(f"📊 Baris: {len(df_uploaded)} | Kolom: {len(df_uploaded.columns)}")
                
                # Preview data
                with st.expander("👁️ Preview Dataset"):
                    st.dataframe(df_uploaded.head(5), use_container_width=True)
            else:
                st.error("❌ Format CSV tidak valid!")
                st.warning("Coba perbaiki format CSV atau hubungi admin.")

# Coba load dataset lokal jika belum ada upload
elif st.session_state["dataset"] is None and CSV_PATH.exists():
    df_local, enc, sep = load_csv_flexible(CSV_PATH)
    if df_local is not None:
        st.session_state["dataset"] = df_local
        st.session_state["dataset_source"] = "local"
        st.sidebar.success(f"✅ Dataset lokal: {CSV_PATH.name}")

# Info dataset yang sedang aktif
if st.session_state["dataset"] is not None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Dataset Aktif")
    
    df_info = st.session_state["dataset"]
    source = st.session_state.get("dataset_source", "unknown")
    
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Total Baris", len(df_info))
    col2.metric("Sumber", "Upload" if source == "uploaded" else "Lokal")
    
    # Validasi data
    if 'Jumlah_Ayam' in df_info.columns:
        valid_rows = len(df_info[df_info['Jumlah_Ayam'] > 0])
        st.sidebar.write(f"✅ Baris valid: **{valid_rows}**")
    
    # Tombol reset (hanya untuk uploaded dataset)
    if source == "uploaded":
        if st.sidebar.button("🔄 Reset Dataset", help="Hapus dataset yang diupload"):
            st.session_state["dataset"] = None
            st.session_state["dataset_source"] = None
            st.rerun()
else:
    st.sidebar.warning("⚠️ Belum ada dataset")
    st.sidebar.info("Upload CSV untuk melihat perbandingan dengan data historis Anda")


# ============================================
# FUNGSI SARAN PAKAR
# ============================================
def generate_saran(kd, dp, kategori):
    s = ""
    
    if kd < 8:
        s += "- **Kepadatan rendah**: Ruang gerak ayam sangat baik, risiko stres rendah.\n"
    elif kd <= 12:
        s += "- **Kepadatan sedang**: Masih aman, jaga ventilasi dan kebersihan litter.\n"
    else:
        s += "- **Kepadatan tinggi**: Risiko heat stress dan amonia meningkat.\n"
    
    if dp < 5:
        s += "- **Deplesi rendah**: Kondisi kesehatan dan manajemen sangat baik.\n"
    elif dp <= 10:
        s += "- **Deplesi sedang**: Evaluasi nutrisi, ventilasi, dan pemerataan pakan.\n"
    else:
        s += "- **Deplesi tinggi**: Indikasi masalah kesehatan atau manajemen.\n"
    
    if kategori == "Layak":
        s += "\n**Kesimpulan**: Kandang dalam kondisi layak. Pertahankan manajemen yang baik dan lakukan monitoring rutin."
    elif kategori == "Kurang Layak":
        s += "\n**Kesimpulan**: Kandang kurang optimal. Perbaiki ventilasi, distribusi pakan, dan pengaturan suhu."
    else:
        s += "\n**Kesimpulan**: Kandang tidak layak. Tindakan korektif segera diperlukan untuk menghindari kerugian."
    
    return s


# ============================================
# PAGE: INPUT
# ============================================
if st.session_state["page"] == "input":
    st.title("🐔 Sistem Pakar Fuzzy Tsukamoto")
    st.subheader("Penilaian Kelayakan Kandang Ayam Pedaging")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 Input Data Kandang")
        
        luas = st.number_input(
            "Luas Kandang (m²)",
            min_value=1.0,
            value=300.0,
            step=10.0,
            help="Total luas kandang dalam meter persegi"
        )
        
        jumlah = st.number_input(
            "Jumlah Ayam Awal",
            min_value=1,
            value=5000,
            step=100,
            help="Jumlah ayam saat mulai periode"
        )
        
        sisa = st.number_input(
            "Sisa Hidup Ayam",
            min_value=0,
            value=4800,
            step=100,
            help="Jumlah ayam yang masih hidup"
        )
    
    with col2:
        st.markdown("### 📊 Preview")
        
        if jumlah > 0 and luas > 0:
            kd_preview = jumlah / luas
            dp_preview = ((jumlah - sisa) / jumlah * 100) if sisa <= jumlah else 0
            
            st.metric("Kepadatan", f"{kd_preview:.2f} ekor/m²")
            st.metric("Deplesi", f"{dp_preview:.2f}%")
            st.metric("Mati", f"{jumlah - sisa:,} ekor")
            
            if kd_preview <= 8:
                st.success("✅ Kepadatan RENDAH")
            elif kd_preview <= 12:
                st.info("ℹ️ Kepadatan SEDANG")
            else:
                st.warning("⚠️ Kepadatan TINGGI")
    
    st.markdown("---")
    
    # Tombol Hitung
    if st.button("🔍 Hitung Kelayakan Kandang", type="primary", use_container_width=True):
        # Validasi
        if sisa > jumlah:
            st.error("❌ Sisa hidup tidak boleh lebih besar dari jumlah awal!")
            st.stop()
        
        # Warning untuk kondisi ekstrem
        if luas < 50:
            st.warning("⚠️ Luas kandang sangat kecil (<50 m²)")
        
        kepadatan_check = jumlah / luas
        if kepadatan_check > 20:
            st.warning(f"⚠️ Kepadatan sangat tinggi ({kepadatan_check:.1f} ekor/m²)!")
        
        deplesi_check = ((jumlah - sisa) / jumlah) * 100
        if deplesi_check > 20:
            st.warning(f"⚠️ Deplesi sangat tinggi ({deplesi_check:.1f}%)!")
        
        # Simpan ke session state
        st.session_state["input_data"] = {
            "luas": luas,
            "jumlah": jumlah,
            "sisa": sisa
        }
        
        st.success("✅ Data tersimpan! Menghitung...")
        go("hasil")
    
    st.stop()


# ============================================
# PAGE: HASIL
# ============================================
if st.session_state["page"] == "hasil":
    
    if st.session_state["input_data"] is None:
        st.warning("⚠️ Belum ada input data")
        if st.button("← Kembali ke Input"):
            go("input")
        st.stop()
    
    # Ambil data input
    x = st.session_state["input_data"]
    
    # KRUSIAL: Ambil dataset dari session state
    df = st.session_state.get("dataset", None)
    
    # Hitung hasil
    out = compute_results(x["luas"], x["jumlah"], x["sisa"], df)
    
    st.title("📊 Hasil Analisis Kelayakan Kandang")
    
    # Hasil Utama
    st.markdown("### 🎯 Hasil Perhitungan")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Kepadatan", f"{out['kepadatan_user']:.2f} ekor/m²")
    col2.metric("Deplesi", f"{out['deplesi_user']:.2f}%")
    col3.metric("Nilai Fuzzy", f"{out['fuzzy_val']:.2f}")
    
    # Kategori
    st.markdown("### 📋 Kategori Kelayakan")
    if out["kategori"] == "Layak":
        st.success(f"✅ **{out['kategori']}** - Kandang dalam kondisi baik")
    elif out["kategori"] == "Kurang Layak":
        st.warning(f"⚠️ **{out['kategori']}** - Perlu perbaikan")
    else:
        st.error(f"❌ **{out['kategori']}** - Perlu tindakan segera")
    
    # Saran Pakar
    st.markdown("### 💡 Saran Pakar")
    st.info(generate_saran(out["kepadatan_user"], out["deplesi_user"], out["kategori"]))
    
    st.markdown("---")
    
    # Perbandingan Dataset
    if out["dataset_present"]:
        st.header("📈 Perbandingan dengan Dataset Historis")
        
        s = out["summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TOTAL AYAM", f"{s['total_ayam']:,}")
        c2.metric("TOTAL MATI", f"{s['total_mati']:,}")
        c3.metric("TOTAL AFKIR", "-")
        c4.metric("RATA KEPADATAN", f"{s['rata_kepadatan']:.2f}")
        
        st.markdown("#### 📊 Grafik Kepadatan per Kandang")
        st.altair_chart(out["chart_kepadatan"], use_container_width=True)
        
        colL, colR = st.columns(2)
        with colL:
            st.markdown("#### 📊 Distribusi Kepadatan")
            st.altair_chart(out["chart_kepadatan_dist"], use_container_width=True)
        
        with colR:
            st.markdown("#### 📊 Distribusi Deplesi")
            st.altair_chart(out["chart_deplesi_dist"], use_container_width=True)
        
        st.markdown("### 🔍 5 Kandang Paling Mirip")
        st.dataframe(out["top_similar"], use_container_width=True)
    
    else:
        st.info("ℹ️ **Tidak ada dataset untuk perbandingan**")
        st.markdown("""
        Untuk melihat perbandingan dengan data historis:
        1. Upload file CSV di sidebar kiri
        2. Pastikan CSV memiliki kolom: `Jumlah_Ayam`, `Kepadatan`, `Deplesi_pct`
        3. Klik tombol "Kembali" dan hitung ulang
        """)
    
    st.markdown("---")
    
    # Tombol navigasi
    col_nav1, col_nav2, col_nav3 = st.columns([2, 1, 2])
    with col_nav1:
        if st.button("← Kembali ke Input", use_container_width=True):
            go("input")