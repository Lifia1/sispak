# pages/1_Hasil_Kelayakan.py
import streamlit as st
import pandas as pd
from hasil_perhitungan import compute_results

st.set_page_config(page_title="Hasil Kelayakan", layout="wide")
st.title("Hasil Perhitungan Fuzzy")

# Ambil input dari session_state jika ada
input_data = st.session_state.get("input_data", None)
df = st.session_state.get("dataset", None)

if input_data is None:
    st.warning("Belum ada input. Kembali ke halaman utama dan isi data lalu tekan 'Hitung Kelayakan'.")
    st.stop()

luas = input_data["luas_m2"]
jumlah_awal = input_data["jumlah_awal"]
sisa_hidup = input_data["sisa_hidup"]

# panggil compute_results dari hasil_perhitungan.py
out = compute_results(luas, jumlah_awal, sisa_hidup, df_dataset=df, top_n=5)

# tampilkan hasil user
c1, c2, c3 = st.columns([1,1,2])
with c1:
    st.markdown(f"**Kepadatan:** `{out['kepadatan_user']:.2f}` ekor/m²" if out['kepadatan_user'] is not None else "Kepadatan: -")
    st.markdown(f"**Deplesi:** `{out['deplesi_user']:.2f}%`" if out['deplesi_user'] is not None else "Deplesi: -")
with c2:
    st.markdown(f"**Nilai Fuzzy:** `{(out['fuzzy_val'] if out['fuzzy_val'] is not None else 0):.2f}`")
    kategori = out['kategori']
    if kategori == "Layak":
        st.success(f"Kategori: ✅ **{kategori}**")
    elif kategori == "Kurang Layak":
        st.warning(f"Kategori: ⚠️ **{kategori}**")
    elif kategori == "Tidak Layak":
        st.error(f"Kategori: ❌ **{kategori}**")
    else:
        st.info(f"Kategori: {kategori}")
with c3:
    if kategori == "Layak":
        st.info("Saran Pakar: Kandang layak. Pertahankan ventilasi dan manajemen.")
    elif kategori == "Kurang Layak":
        st.info("Saran Pakar: Perbaiki ventilasi atau kurangi kepadatan.")
    else:
        st.info("Saran Pakar: Kandang tidak layak. Kurangi kepadatan atau pisah kandang.")

# jika ada dataset tampilkan perbandingan
if out.get("dataset_present"):
    st.markdown("---")
    st.header("Perbandingan dengan Dataset")
    s = out["summary"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TOTAL AYAM", f"{s['total_ayam']:,}")
    k2.metric("TOTAL MATI", f"{s['total_mati']:,}")
    k3.metric("TOTAL AFKIR", "-")
    k4.metric("RATA KEPADATAN (ekor/m²)", f"{s['rata_kepadatan']:.2f}")

    if out["chart_kepadatan"] is not None:
        st.altair_chart(out["chart_kepadatan"], use_container_width=True)

    st.markdown("### Top 5 Kandang Paling Mirip (berdasarkan kepadatan)")
    if out["top_similar"] is not None:
        st.dataframe(out["top_similar"].round(3))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("Distribusi Kepadatan (dataset)")
        if out["chart_kepadatan_dist"] is not None:
            st.altair_chart(out["chart_kepadatan_dist"], use_container_width=True)
    with c2:
        st.markdown("Distribusi Deplesi (dataset)")
        if out["chart_deplesi_dist"] is not None:
            st.altair_chart(out["chart_deplesi_dist"], use_container_width=True)
else:
    st.info("Tidak ada dataset untuk dibandingkan. Kembali ke halaman utama dan upload CSV jika ingin perbandingan.")
