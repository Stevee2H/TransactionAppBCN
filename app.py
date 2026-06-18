import streamlit as st
import pandas as pd
from db import (
    init_db, get_conn,
    get_items, get_lantai, get_sesi,
    upsert_distribusi, get_distribusi,
    add_transaksi, delete_transaksi, get_transaksi,
    get_saldo_per_item, get_barang_belum_kembali,
    get_rincian_per_lantai, update_stok, update_tipe
)

st.set_page_config(page_title="Camp Inventory", page_icon="📦", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .alert-red   { background:#ffe0e0; border-left:4px solid #e53935;
                   padding:.6rem 1rem; border-radius:6px; margin:.4rem 0; }
    .alert-green { background:#e0f7e9; border-left:4px solid #43a047;
                   padding:.6rem 1rem; border-radius:6px; margin:.4rem 0; }
    .stTabs [data-baseweb="tab"] { font-size:15px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("📦 Camp Inventory")
    st.subheader("Login Admin")
    with st.form("login_form"):
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Masuk", use_container_width=True):
            if pw == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.logged_in = True
                init_db()
                st.rerun()
            else:
                st.error("Password salah.")
    st.stop()

# ─────────────────────────────────────────────
# MAIN APP (setelah login)
# ─────────────────────────────────────────────
col_title, col_logout = st.columns([6, 1])
col_title.title("📦 Camp Inventory")
if col_logout.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📥 Input Transaksi",
    "🏠 Distribusi Awal",
    "📋 History",
    "⚙️ Master Data",
])

# ─────────────────────────────────────────────
# TAB 1 — DASHBOARD
# ─────────────────────────────────────────────
with tab1:
    conn = get_conn()
    saldo_rows    = get_saldo_per_item(conn)
    belum_kembali = get_barang_belum_kembali(conn)
    items_all     = get_items(conn)
    conn.close()

    st.subheader("Ringkasan Stok")
    df_saldo = pd.DataFrame(saldo_rows)

    if not df_saldo.empty:
        consumable = df_saldo[df_saldo["tipe"] == "consumable"]
        belum_df   = pd.DataFrame(belum_kembali)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Jenis Barang", len(df_saldo))
        c2.metric("⚠️ Returnable Belum Kembali", len(belum_df) if not belum_df.empty else 0)
        c3.metric("Jenis Consumable", len(consumable))

        st.divider()

        if not belum_df.empty:
            st.subheader("⚠️ Barang Returnable Belum Kembali")
            for _, row in belum_df.iterrows():
                st.markdown(
                    f'<div class="alert-red">🔴 <b>{row["nama"]}</b> '
                    f'— {int(row["total_di_luar"])} unit masih di luar</div>',
                    unsafe_allow_html=True
                )
            st.divider()
        else:
            st.markdown(
                '<div class="alert-green">✅ Semua barang returnable sudah kembali!</div>',
                unsafe_allow_html=True
            )
            st.divider()

        st.subheader("Detail Stok Semua Barang")
        display = df_saldo[["id","nama","tipe","stok","total_distribusi","net_transaksi","saldo_gudang"]].copy()
        display.columns = ["ID","Nama Barang","Tipe","Stok Awal","Distribusi Awal","Net Transaksi","Sisa di Gudang"]

        def color_saldo(val):
            if isinstance(val, (int, float)):
                if val < 0:  return "background-color:#ffe0e0"
                if val == 0: return "background-color:#fff9c4"
            return ""

        st.dataframe(
            display.style.map(color_saldo, subset=["Sisa di Gudang"]),
            use_container_width=True, hide_index=True
        )

        st.divider()
        st.subheader("📍 Rincian Lokasi Barang")
        selected_item = st.selectbox(
            "Pilih barang:",
            options=[r["id"] for r in items_all],
            format_func=lambda x: next(r["nama"] for r in items_all if r["id"] == x)
        )
        conn = get_conn()
        rincian = get_rincian_per_lantai(conn, selected_item)
        conn.close()
        if rincian:
            df_rin = pd.DataFrame(rincian)
            df_rin.columns = ["Lantai", "Jumlah di Lantai"]
            st.dataframe(df_rin, use_container_width=True, hide_index=True)
        else:
            st.markdown(
                '<div class="alert-green">✅ Tidak ada di lantai manapun saat ini</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Belum ada data. Mulai dengan mengisi stok di tab ⚙️ Master Data.")

# ─────────────────────────────────────────────
# TAB 2 — INPUT TRANSAKSI
# ─────────────────────────────────────────────
with tab2:
    st.subheader("Input Transaksi Peminjaman / Pengembalian")
    conn      = get_conn()
    lantai_all = get_lantai(conn)
    sesi_all   = get_sesi(conn)
    items_all  = get_items(conn)
    conn.close()

    with st.form("form_transaksi", clear_on_submit=True):
        c1, c2 = st.columns(2)
        hari = c1.selectbox("Hari", [1,2,3], format_func=lambda x: f"Day {x}")
        id_sesi = c2.selectbox(
            "Sesi",
            options=[r["id"] for r in sesi_all],
            format_func=lambda x: next(f"{r['jam']} — {r['nama']}" for r in sesi_all if r["id"] == x)
        )
        c3, c4 = st.columns(2)
        id_lantai = c3.selectbox(
            "Lantai",
            options=[r["id"] for r in lantai_all],
            format_func=lambda x: next(r["nama"] for r in lantai_all if r["id"] == x)
        )
        id_item = c4.selectbox(
            "Barang",
            options=[r["id"] for r in items_all],
            format_func=lambda x: next(r["nama"] for r in items_all if r["id"] == x)
        )
        c5, c6 = st.columns(2)
        jumlah  = c5.number_input("Jumlah (+ keluar, - kembali)", step=1, value=1)
        catatan = c6.text_input("Catatan (opsional)")

        if st.form_submit_button("✅ Simpan Transaksi", use_container_width=True):
            conn = get_conn()
            add_transaksi(conn, hari, id_sesi, id_lantai, id_item, jumlah, catatan)
            conn.close()
            st.success(f"{'Keluar' if jumlah > 0 else 'Kembali'}: {abs(jumlah)} unit disimpan!")
            st.rerun()

# ─────────────────────────────────────────────
# TAB 3 — DISTRIBUSI AWAL
# ─────────────────────────────────────────────
with tab3:
    st.subheader("Distribusi Awal Stok ke Lantai")
    st.caption("Isi berapa banyak tiap barang yang diberikan ke tiap lantai di awal camp.")

    conn       = get_conn()
    lantai_all = get_lantai(conn)
    items_all  = get_items(conn)
    conn.close()

    with st.form("form_distribusi", clear_on_submit=True):
        c1, c2 = st.columns(2)
        id_lantai_d = c1.selectbox(
            "Lantai",
            options=[r["id"] for r in lantai_all],
            format_func=lambda x: next(r["nama"] for r in lantai_all if r["id"] == x),
            key="dist_lantai"
        )
        id_item_d = c2.selectbox(
            "Barang",
            options=[r["id"] for r in items_all],
            format_func=lambda x: next(r["nama"] for r in items_all if r["id"] == x),
            key="dist_item"
        )
        jumlah_d = st.number_input("Jumlah yang diberikan", min_value=0, step=1, value=0)
        if st.form_submit_button("💾 Simpan Distribusi", use_container_width=True):
            conn = get_conn()
            upsert_distribusi(conn, id_lantai_d, id_item_d, jumlah_d)
            conn.close()
            st.success("Distribusi disimpan!")
            st.rerun()

    st.divider()
    st.subheader("Data Distribusi Awal")
    conn      = get_conn()
    dist_rows = get_distribusi(conn)
    conn.close()
    if dist_rows:
        df_dist = pd.DataFrame(dist_rows)
        df_dist = df_dist[["id_lantai","nama_lantai","id_item","nama_item","jumlah"]]
        df_dist.columns = ["ID Lantai","Lantai","ID Barang","Barang","Jumlah"]
        df_dist = df_dist[df_dist["Jumlah"] > 0]
        st.dataframe(df_dist, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada distribusi awal.")

# ─────────────────────────────────────────────
# TAB 4 — HISTORY
# ─────────────────────────────────────────────
with tab4:
    st.subheader("History Transaksi")
    conn       = get_conn()
    lantai_all = get_lantai(conn)
    conn.close()

    c1, c2 = st.columns(2)
    filter_hari   = c1.selectbox("Filter Hari", [0,1,2,3],
                                  format_func=lambda x: "Semua" if x == 0 else f"Day {x}")
    filter_lantai = c2.selectbox(
        "Filter Lantai",
        options=[""] + [r["id"] for r in lantai_all],
        format_func=lambda x: "Semua" if x == "" else next(r["nama"] for r in lantai_all if r["id"] == x)
    )

    conn = get_conn()
    rows = get_transaksi(
        conn,
        hari=filter_hari if filter_hari != 0 else None,
        id_lantai=filter_lantai if filter_lantai != "" else None
    )
    conn.close()

    if rows:
        df_trx = pd.DataFrame(rows)
        df_trx = df_trx[["id","hari","jam","nama_sesi","nama_lantai","nama_item","jumlah","catatan","created_at"]]
        df_trx.columns = ["ID","Hari","Jam","Sesi","Lantai","Barang","Jumlah","Catatan","Waktu Input"]
        df_trx["Hari"] = df_trx["Hari"].apply(lambda x: f"Day {x}")

        def color_jumlah(val):
            if isinstance(val, (int, float)):
                return "color:#e53935;font-weight:bold" if val > 0 else "color:#43a047;font-weight:bold"
            return ""

        st.dataframe(
            df_trx.style.map(color_jumlah, subset=["Jumlah"]),
            use_container_width=True, hide_index=True
        )

        st.divider()
        st.subheader("🗑️ Hapus Transaksi")
        st.caption("Gunakan jika ada salah input. Lihat ID dari tabel di atas.")
        del_id = st.number_input("ID transaksi yang ingin dihapus", min_value=1, step=1)
        if st.button("Hapus", type="secondary"):
            conn = get_conn()
            delete_transaksi(conn, del_id)
            conn.close()
            st.success(f"Transaksi ID {del_id} dihapus.")
            st.rerun()
    else:
        st.info("Belum ada transaksi.")

# ─────────────────────────────────────────────
# TAB 5 — MASTER DATA
# ─────────────────────────────────────────────
with tab5:
    st.subheader("⚙️ Master Data Barang")
    st.caption("Set stok awal dan tipe tiap barang. Tipe menentukan apakah barang harus dikembalikan.")

    conn      = get_conn()
    items_all = get_items(conn)
    conn.close()

    for row in items_all:
        with st.expander(f"{row['id']} — {row['nama']}"):
            c1, c2, c3 = st.columns(3)
            new_stok = c1.number_input("Stok Awal", value=int(row["stok"]),
                                        min_value=0, key=f"stok_{row['id']}")
            new_tipe = c2.selectbox("Tipe", ["returnable","consumable"],
                                     index=0 if row["tipe"] == "returnable" else 1,
                                     key=f"tipe_{row['id']}")
            if c3.button("💾 Simpan", key=f"save_{row['id']}"):
                conn = get_conn()
                update_stok(conn, row["id"], new_stok)
                update_tipe(conn, row["id"], new_tipe)
                conn.close()
                st.success("Disimpan!")
                st.rerun()
