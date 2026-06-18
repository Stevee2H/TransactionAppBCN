import streamlit as st
import pandas as pd
from db import (
    get_items, get_lantai, get_sesi,
    upsert_distribusi, get_distribusi,
    add_transaksi, delete_transaksi, get_transaksi,
    get_saldo_per_item, get_barang_belum_kembali,
    get_rincian_per_lantai, update_stok, update_tipe
)

st.set_page_config(page_title="Camp Inventory", page_icon="📦", layout="wide")
st.markdown("""
<style>
    .block-container { padding-top: 4rem; }
    .stApp > .main > div { padding-top: 0 !important; }
    .alert-red   { background:#ffe0e0; border-left:4px solid #e53935;
                   padding:.6rem 1rem; border-radius:6px; margin:.4rem 0; }
    .alert-green { background:#e0f7e9; border-left:4px solid #43a047;
                   padding:.6rem 1rem; border-radius:6px; margin:.4rem 0; }
    .stTabs [data-baseweb="tab"] { font-size:15px; font-weight:600; }
    .role-badge-admin  { background:#1976d2; color:white; padding:2px 10px;
                         border-radius:20px; font-size:13px; font-weight:600; }
    .role-badge-viewer { background:#757575; color:white; padding:2px 10px;
                         border-radius:20px; font-size:13px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "role" not in st.session_state:
    st.session_state.role = "viewer"  # default: viewer

is_admin = st.session_state.role == "admin"

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
col_title, col_role, col_refresh, col_btn = st.columns([5, 1, 1, 1])
col_title.title("📦 Camp Inventory")

if col_refresh.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

if is_admin:
    col_role.markdown('<div style="padding-top:18px"><span class="role-badge-admin">👤 Admin</span></div>',
                      unsafe_allow_html=True)
    if col_btn.button("Logout"):
        st.session_state.role = "viewer"
        st.rerun()
else:
    col_role.markdown('<div style="padding-top:18px"><span class="role-badge-viewer">👁 Viewer</span></div>',
                      unsafe_allow_html=True)
    if col_btn.button("Login Admin"):
        st.session_state.show_login = True

# Login modal (hanya muncul kalau klik "Login Admin")
if not is_admin and st.session_state.get("show_login", False):
    with st.expander("🔐 Login sebagai Admin", expanded=True):
        with st.form("login_form"):
            pw = st.text_input("Password", type="password")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Masuk", use_container_width=True):
                if pw == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state.role = "admin"
                    st.session_state.show_login = False
                    st.rerun()
                else:
                    st.error("Password salah.")
            if c2.form_submit_button("Batal", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()

# ─────────────────────────────────────────────
# TABS — viewer hanya lihat tab 1 & 4
# ─────────────────────────────────────────────
if is_admin:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", "📥 Input Transaksi",
        "🏠 Distribusi Awal", "📋 History", "⚙️ Master Data",
    ])
else:
    tab1, tab4 = st.tabs(["📊 Dashboard", "📋 History"])

# ─────────────────────────────────────────────
# TAB 1 — DASHBOARD
# ─────────────────────────────────────────────
with tab1:
    @st.cache_data(ttl=30)
    def load_dashboard():
        return get_saldo_per_item(), get_barang_belum_kembali(), get_items()

    saldo_rows, belum_kembali, items_all = load_dashboard()
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
                    f'— {int(row["total_keluar"])} unit masih di luar</div>',
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

        @st.cache_data(ttl=30)
        def load_rincian(item_id):
            return get_rincian_per_lantai(item_id)

        selected_item = st.selectbox(
            "Pilih barang:",
            options=[r["id"] for r in items_all],
            format_func=lambda x: next(r["nama"] for r in items_all if r["id"] == x)
        )
        rincian = load_rincian(selected_item)
        if rincian:
            st.dataframe(pd.DataFrame(rincian).rename(columns={
                "nama_lantai": "Lantai", "jumlah_di_lantai": "Jumlah di Lantai"
            }), use_container_width=True, hide_index=True)
        else:
            st.markdown(
                '<div class="alert-green">✅ Tidak ada di lantai manapun saat ini</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Belum ada data. Admin perlu mengisi stok di tab ⚙️ Master Data.")

# ─────────────────────────────────────────────
# TAB 2 — INPUT TRANSAKSI (admin only)
# ─────────────────────────────────────────────
if is_admin:
    with tab2:
        st.subheader("Input Transaksi Peminjaman / Pengembalian")

        @st.cache_data(ttl=60)
        def load_form_data():
            return get_lantai(), get_sesi(), get_items()

        lantai_all, sesi_all, items_all = load_form_data()

        with st.form("form_transaksi", clear_on_submit=True):
            c1, c2 = st.columns(2)
            hari    = c1.selectbox("Hari", [1,2,3], format_func=lambda x: f"Day {x}")
            sesi_filtered = [r for r in sesi_all if r["hari"] == hari]
            id_sesi = c2.selectbox(
                "Sesi",
                options=[r["id"] for r in sesi_filtered],
                format_func=lambda x: next(f"{r['jam']} — {r['nama']}" for r in sesi_filtered if r["id"] == x)
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
            c5, c6  = st.columns(2)
            jumlah  = c5.number_input("Jumlah (+ keluar, - kembali)", step=1, value=1)
            catatan = c6.text_input("Catatan (opsional)")

            if st.form_submit_button("✅ Simpan Transaksi", use_container_width=True):
                add_transaksi(hari, id_sesi, id_lantai, id_item, jumlah, catatan)
                st.cache_data.clear()
                st.success(f"{'Keluar' if jumlah > 0 else 'Kembali'}: {abs(jumlah)} unit disimpan!")
                st.rerun()

# ─────────────────────────────────────────────
# TAB 3 — DISTRIBUSI AWAL (admin only)
# ─────────────────────────────────────────────
if is_admin:
    with tab3:
        st.subheader("Distribusi Awal Stok ke Lantai")
        st.caption("Isi berapa banyak tiap barang yang diberikan ke tiap lantai di awal camp.")

        @st.cache_data(ttl=60)
        def load_dist_data():
            return get_lantai(), get_items()

        lantai_all, items_all = load_dist_data()

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
                upsert_distribusi(id_lantai_d, id_item_d, jumlah_d)
                st.cache_data.clear()
                st.success("Distribusi disimpan!")
                st.rerun()

        st.divider()
        st.subheader("Data Distribusi Awal")

        @st.cache_data(ttl=30)
        def load_distribusi():
            return get_distribusi()

        dist_rows = load_distribusi()
        if dist_rows:
            rows_display = []
            for r in dist_rows:
                if r["jumlah"] > 0:
                    rows_display.append({
                        "ID Lantai": r["id_lantai"],
                        "Lantai":    r["lantai"]["nama"],
                        "ID Barang": r["id_item"],
                        "Barang":    r["item"]["nama"],
                        "Jumlah":    r["jumlah"],
                    })
            if rows_display:
                st.dataframe(pd.DataFrame(rows_display), use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada distribusi awal.")
        else:
            st.info("Belum ada distribusi awal.")

# ─────────────────────────────────────────────
# TAB 4 — HISTORY (admin & viewer)
# ─────────────────────────────────────────────
with tab4:
    st.subheader("History Transaksi")

    @st.cache_data(ttl=30)
    def load_lantai():
        return get_lantai()

    lantai_all = load_lantai()

    c1, c2 = st.columns(2)
    filter_hari   = c1.selectbox("Filter Hari", [0,1,2,3],
                                  format_func=lambda x: "Semua" if x == 0 else f"Day {x}")
    filter_lantai = c2.selectbox(
        "Filter Lantai",
        options=[""] + [r["id"] for r in lantai_all],
        format_func=lambda x: "Semua" if x == "" else next(r["nama"] for r in lantai_all if r["id"] == x)
    )

    @st.cache_data(ttl=30)
    def load_transaksi(hari, id_lantai):
        return get_transaksi(
            hari=hari if hari != 0 else None,
            id_lantai=id_lantai if id_lantai != "" else None
        )

    rows = load_transaksi(filter_hari, filter_lantai)

    if rows:
        rows_display = []
        for r in rows:
            rows_display.append({
                "ID":      r["id"],
                "Hari":    f"Day {r['hari']}",
                "Jam":     r["sesi"]["jam"],
                "Sesi":    r["sesi"]["nama"],
                "Lantai":  r["lantai"]["nama"],
                "Barang":  r["item"]["nama"],
                "Jumlah":  r["jumlah"],
                "Catatan": r["catatan"],
                "Waktu":   r["created_at"],
            })
        df_trx = pd.DataFrame(rows_display)

        def color_jumlah(val):
            if isinstance(val, (int, float)):
                return "color:#e53935;font-weight:bold" if val > 0 else "color:#43a047;font-weight:bold"
            return ""

        st.dataframe(
            df_trx.style.map(color_jumlah, subset=["Jumlah"]),
            use_container_width=True, hide_index=True
        )

        # Hapus transaksi — admin only
        if is_admin:
            st.divider()
            st.subheader("🗑️ Hapus Transaksi")
            st.caption("Gunakan jika ada salah input. Lihat ID dari tabel di atas.")
            del_id = st.number_input("ID transaksi yang ingin dihapus", min_value=1, step=1)
            if st.button("Hapus", type="secondary"):
                delete_transaksi(del_id)
                st.cache_data.clear()
                st.success(f"Transaksi ID {del_id} dihapus.")
                st.rerun()
    else:
        st.info("Belum ada transaksi.")

# ─────────────────────────────────────────────
# TAB 5 — MASTER DATA (admin only)
# ─────────────────────────────────────────────
if is_admin:
    with tab5:
        st.subheader("⚙️ Master Data Barang")
        st.caption("Set stok awal dan tipe tiap barang.")

        @st.cache_data(ttl=60)
        def load_items():
            return get_items()

        items_all = load_items()
        for row in items_all:
            with st.expander(f"{row['id']} — {row['nama']}"):
                c1, c2, c3 = st.columns(3)
                new_stok = c1.number_input("Stok Awal", value=int(row["stok"]),
                                            min_value=0, key=f"stok_{row['id']}")
                new_tipe = c2.selectbox("Tipe", ["returnable","consumable"],
                                         index=0 if row["tipe"] == "returnable" else 1,
                                         key=f"tipe_{row['id']}")
                if c3.button("💾 Simpan", key=f"save_{row['id']}"):
                    update_stok(row["id"], new_stok)
                    update_tipe(row["id"], new_tipe)
                    st.cache_data.clear()
                    st.success("Disimpan!")
                    st.rerun()
