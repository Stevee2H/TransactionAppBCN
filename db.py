from supabase import create_client
import streamlit as st

@st.cache_resource
def get_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

# ── Item ──────────────────────────────────────
def get_items():
    res = get_client().table("item").select("*").order("id").execute()
    return res.data

def update_stok(id_item, stok):
    get_client().table("item").update({"stok": stok}).eq("id", id_item).execute()

def update_tipe(id_item, tipe):
    get_client().table("item").update({"tipe": tipe}).eq("id", id_item).execute()

# ── Lantai ────────────────────────────────────
def get_lantai():
    res = get_client().table("lantai").select("*").order("id").execute()
    return res.data

# ── Sesi ──────────────────────────────────────
def get_sesi(hari=None):
    q = get_client().table("sesi").select("*").order("jam")
    if hari:
        q = q.eq("hari", hari)
    return q.execute().data

# ── Distribusi ────────────────────────────────
def upsert_distribusi(id_lantai, id_item, jumlah):
    get_client().table("distribusi").upsert({
        "id_lantai": id_lantai,
        "id_item": id_item,
        "jumlah": jumlah
    }, on_conflict="id_lantai,id_item").execute()

def get_distribusi():
    res = get_client().table("distribusi")\
        .select("*, lantai(nama), item(nama)")\
        .order("id_lantai").execute()
    return res.data

# ── Transaksi ─────────────────────────────────
def add_transaksi(hari, id_sesi, id_lantai, id_item, jumlah, catatan=""):
    get_client().table("transaksi").insert({
        "hari": hari,
        "id_sesi": id_sesi,
        "id_lantai": id_lantai,
        "id_item": id_item,
        "jumlah": jumlah,
        "catatan": catatan
    }).execute()

def delete_transaksi(trx_id):
    get_client().table("transaksi").delete().eq("id", trx_id).execute()

def get_transaksi(hari=None, id_lantai=None):
    q = get_client().table("transaksi")\
        .select("*, sesi(jam, nama), lantai(nama), item(nama)")\
        .order("hari").order("id")
    if hari:
        q = q.eq("hari", hari)
    if id_lantai:
        q = q.eq("id_lantai", id_lantai)
    return q.execute().data

def get_saldo_per_item():
    items    = get_items()
    dist_res = get_client().table("distribusi").select("id_item, jumlah").execute().data
    trx_res  = get_client().table("transaksi").select("id_item, jumlah").execute().data

    # Aggregate distribusi
    dist_map = {}
    for d in dist_res:
        dist_map[d["id_item"]] = dist_map.get(d["id_item"], 0) + d["jumlah"]

    # Aggregate transaksi
    trx_map = {}
    for t in trx_res:
        trx_map[t["id_item"]] = trx_map.get(t["id_item"], 0) + t["jumlah"]

    result = []
    for item in items:
        iid  = item["id"]
        dist = dist_map.get(iid, 0)
        net  = trx_map.get(iid, 0)
        result.append({
            "id":               iid,
            "nama":             item["nama"],
            "tipe":             item["tipe"],
            "stok":             item["stok"],
            "total_distribusi": dist,
            "net_transaksi":    net,
            "saldo_gudang":     item["stok"] - dist - net,
            "total_keluar":     dist + net,
        })
    return result

def get_barang_belum_kembali():
    saldo = get_saldo_per_item()
    return [r for r in saldo if r["tipe"] == "returnable" and r["total_keluar"] > 0]

def get_rincian_per_lantai(id_item):
    lantai   = get_lantai()
    dist_res = get_client().table("distribusi").select("id_lantai, jumlah")\
                   .eq("id_item", id_item).execute().data
    trx_res  = get_client().table("transaksi").select("id_lantai, jumlah")\
                   .eq("id_item", id_item).execute().data

    dist_map = {d["id_lantai"]: d["jumlah"] for d in dist_res}
    trx_map  = {}
    for t in trx_res:
        trx_map[t["id_lantai"]] = trx_map.get(t["id_lantai"], 0) + t["jumlah"]

    result = []
    for lt in lantai:
        lid   = lt["id"]
        total = dist_map.get(lid, 0) + trx_map.get(lid, 0)
        if total > 0:
            result.append({"nama_lantai": lt["nama"], "jumlah_di_lantai": total})
    return result
