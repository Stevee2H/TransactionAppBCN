# Camp Inventory App

## Setup

### 1. Isi Supabase connection string
Edit `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
ADMIN_PASSWORD = "password_admin_kamu"
```

### 2. Jalankan schema di Supabase
- Buka Supabase Dashboard → SQL Editor
- Copy-paste isi `schema.sql` → Run

### 3. Deploy ke Streamlit Cloud
- Push repo ini ke GitHub
- Buka share.streamlit.io → New app → pilih repo ini
- Di bagian Secrets, isi sama seperti secrets.toml

### 4. Jalankan lokal (opsional)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Alur Penggunaan
1. **Master Data** — isi stok awal tiap barang
2. **Distribusi Awal** — input berapa yang diberikan ke tiap lantai
3. **Input Transaksi** — setiap ada peminjaman/pengembalian tambahan
4. **Dashboard** — pantau saldo & alert barang belum kembali
5. **History** — lihat semua transaksi, hapus jika salah input
