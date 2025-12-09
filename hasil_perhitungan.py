import pandas as pd
import numpy as np
import altair as alt

# ==============================
#   FUNGSI KEANGGOTAAN FUZZY
# ==============================

def kepadatan_rendah(x):
    """Kepadatan rendah: ideal untuk kesehatan ayam"""
    if x <= 8: return 1
    if 8 < x < 12: return (12 - x) / 4
    return 0

def kepadatan_sedang(x):
    """Kepadatan sedang: masih dapat diterima"""
    if 8 <= x <= 12: return (x - 8) / 4
    if 12 < x <= 16: return (16 - x) / 4
    return 0

def kepadatan_tinggi(x):
    """Kepadatan tinggi: berisiko untuk kesehatan"""
    if x <= 12: return 0
    if 12 < x < 16: return (x - 12) / 4
    return 1

def deplesi_rendah(x):
    """Deplesi rendah: mortalitas minimal"""
    if x <= 5: return 1
    if 5 < x < 10: return (10 - x) / 5
    return 0

def deplesi_sedang(x):
    """Deplesi sedang: perlu perhatian"""
    if 5 <= x <= 10: return (x - 5) / 5
    if 10 < x <= 15: return (15 - x) / 5
    return 0

def deplesi_tinggi(x):
    """Deplesi tinggi: kondisi berbahaya"""
    if x <= 10: return 0
    if 10 < x < 15: return (x - 10) / 5
    return 1

# ==============================
#   OUTPUT FUZZY (NILAI KELAYAKAN)
# ==============================
# Semakin TINGGI nilai = Semakin LAYAK kandang
# Range: 0-100

def output_tinggi(a):
    """Kondisi sangat baik → Nilai kelayakan tinggi"""
    return 70 + a * 30  # 70-100

def output_sedang(a):
    """Kondisi cukup baik → Nilai kelayakan sedang"""
    return 40 + a * 30  # 40-70

def output_rendah(a):
    """Kondisi buruk → Nilai kelayakan rendah"""
    return 10 + a * 30  # 10-40


# ==============================
#   PERHITUNGAN UTAMA (DIPERBAIKI)
# ==============================
def compute_results(luas, jumlah_awal, sisa_hidup, df_dataset=None):

    # 1. Perhitungan mortalitas + deplesi
    mati = max(jumlah_awal - sisa_hidup, 0)
    deplesi = 0 if jumlah_awal == 0 else (mati / jumlah_awal) * 100
    kepadatan = jumlah_awal / luas

    # 2. Keanggotaan fuzzy
    μ_k_r = kepadatan_rendah(kepadatan)
    μ_k_s = kepadatan_sedang(kepadatan)
    μ_k_t = kepadatan_tinggi(kepadatan)

    μ_d_r = deplesi_rendah(deplesi)
    μ_d_s = deplesi_sedang(deplesi)
    μ_d_t = deplesi_tinggi(deplesi)

    # ==============================
    # 3. RULE FUZZY TSUKAMOTO (9 RULE LENGKAP)
    # ==============================
    rules = []
    alphas = []
    
    # RULE 1: Kepadatan Rendah + Deplesi Rendah → SANGAT LAYAK
    α1 = min(μ_k_r, μ_d_r)
    if α1 > 0:
        z1 = output_tinggi(α1)
        rules.append(α1 * z1)
        alphas.append(α1)
    
    # RULE 2: Kepadatan Rendah + Deplesi Sedang → LAYAK
    α2 = min(μ_k_r, μ_d_s)
    if α2 > 0:
        z2 = output_sedang(α2)
        rules.append(α2 * z2)
        alphas.append(α2)
    
    # RULE 3: Kepadatan Rendah + Deplesi Tinggi → KURANG LAYAK
    α3 = min(μ_k_r, μ_d_t)
    if α3 > 0:
        z3 = output_rendah(α3)
        rules.append(α3 * z3)
        alphas.append(α3)
    
    # RULE 4: Kepadatan Sedang + Deplesi Rendah → LAYAK
    α4 = min(μ_k_s, μ_d_r)
    if α4 > 0:
        z4 = output_sedang(α4)
        rules.append(α4 * z4)
        alphas.append(α4)
    
    # RULE 5: Kepadatan Sedang + Deplesi Sedang → KURANG LAYAK
    α5 = min(μ_k_s, μ_d_s)
    if α5 > 0:
        z5 = output_rendah(α5)
        rules.append(α5 * z5)
        alphas.append(α5)
    
    # RULE 6: Kepadatan Sedang + Deplesi Tinggi → TIDAK LAYAK
    α6 = min(μ_k_s, μ_d_t)
    if α6 > 0:
        z6 = output_rendah(α6) * 0.7  # Lebih rendah dari rule 5
        rules.append(α6 * z6)
        alphas.append(α6)
    
    # RULE 7: Kepadatan Tinggi + Deplesi Rendah → KURANG LAYAK
    α7 = min(μ_k_t, μ_d_r)
    if α7 > 0:
        z7 = output_rendah(α7)
        rules.append(α7 * z7)
        alphas.append(α7)
    
    # RULE 8: Kepadatan Tinggi + Deplesi Sedang → TIDAK LAYAK
    α8 = min(μ_k_t, μ_d_s)
    if α8 > 0:
        z8 = output_rendah(α8) * 0.6
        rules.append(α8 * z8)
        alphas.append(α8)
    
    # RULE 9: Kepadatan Tinggi + Deplesi Tinggi → SANGAT TIDAK LAYAK
    α9 = min(μ_k_t, μ_d_t)
    if α9 > 0:
        z9 = output_rendah(α9) * 0.5
        rules.append(α9 * z9)
        alphas.append(α9)

    # Defuzzifikasi (Weighted Average)
    fuzzy_val = (sum(rules) / sum(alphas)) if len(alphas) > 0 else 0

    # 4. Kategori akhir (threshold disesuaikan)
    if fuzzy_val >= 60:
        kategori = "Layak"
    elif fuzzy_val >= 35:
        kategori = "Kurang Layak"
    else:
        kategori = "Tidak Layak"

    # Jika dataset tidak ada
    if df_dataset is None:
        return {
            "kepadatan_user": kepadatan,
            "deplesi_user": deplesi,
            "fuzzy_val": fuzzy_val,
            "kategori": kategori,
            "dataset_present": False
        }

    # ==============================
    #   PENGOLAHAN DATASET
    # ==============================
    df = df_dataset.copy()

    # Perbaikan nilai nol pada deplesi
    df["Deplesi_pct"] = df["Deplesi_pct"].fillna(0).replace(0, 0.0001)

    # Ringkasan dataset
    summary = {
        "total_ayam": int(df["Jumlah_Ayam"].sum()),
        "total_mati": int(df["Mati"].dropna().sum()),
        "rata_kepadatan": df["Kepadatan"].mean()
    }

    # Chart kepadatan per kandang
    chart_kepadatan = (
        alt.Chart(df)
        .mark_bar(color="#69b3a2")
        .encode(
            x=alt.X("No:O", title="Kandang"),
            y=alt.Y("Kepadatan:Q", title="Kepadatan (ekor/m²)"),
            tooltip=["Kandang", "Kepadatan", "Deplesi_pct"]
        )
        .properties(title="Kepadatan per Kandang")
    )

    # Distribusi kepadatan
    chart_kepadatan_dist = (
        alt.Chart(df)
        .mark_bar(color="#4682B4")
        .encode(
            x=alt.X("Kepadatan:Q", bin=alt.Bin(maxbins=15), title="Kepadatan (ekor/m²)"),
            y=alt.Y("count()", title="Jumlah Kandang")
        )
        .properties(title="Distribusi Kepadatan")
    )

    # Distribusi deplesi
    chart_deplesi_dist = (
        alt.Chart(df)
        .mark_bar(color="#ff6666")
        .encode(
            x=alt.X("Deplesi_pct:Q", bin=alt.Bin(maxbins=15), title="Deplesi (%)"),
            y=alt.Y("count()", title="Jumlah Kandang")
        )
        .properties(title="Distribusi Deplesi")
    )

    # Cari kandang paling mirip
    df["selisih"] = (df["Kepadatan"] - kepadatan).abs()
    top_similar = df.nsmallest(5, "selisih")[["No", "Kandang", "Kepadatan", "Deplesi_pct"]].reset_index(drop=True)

    return {
        "kepadatan_user": kepadatan,
        "deplesi_user": deplesi,
        "fuzzy_val": fuzzy_val,
        "kategori": kategori,
        "dataset_present": True,
        "summary": summary,
        "chart_kepadatan": chart_kepadatan,
        "chart_kepadatan_dist": chart_kepadatan_dist,
        "chart_deplesi_dist": chart_deplesi_dist,
        "top_similar": top_similar
    }