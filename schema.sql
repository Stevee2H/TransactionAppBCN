-- PostgreSQL version

CREATE TABLE IF NOT EXISTS item (
    id      TEXT PRIMARY KEY,
    nama    TEXT NOT NULL,
    stok    INTEGER NOT NULL DEFAULT 0,
    tipe    TEXT NOT NULL DEFAULT 'returnable'
);

CREATE TABLE IF NOT EXISTS lantai (
    id      TEXT PRIMARY KEY,
    nama    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sesi (
    id      TEXT PRIMARY KEY,
    jam     TEXT NOT NULL,
    nama    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS distribusi (
    id          SERIAL PRIMARY KEY,
    id_lantai   TEXT NOT NULL REFERENCES lantai(id),
    id_item     TEXT NOT NULL REFERENCES item(id),
    jumlah      INTEGER NOT NULL DEFAULT 0,
    UNIQUE(id_lantai, id_item)
);

CREATE TABLE IF NOT EXISTS transaksi (
    id          SERIAL PRIMARY KEY,
    hari        INTEGER NOT NULL,
    id_sesi     TEXT NOT NULL REFERENCES sesi(id),
    id_lantai   TEXT NOT NULL REFERENCES lantai(id),
    id_item     TEXT NOT NULL REFERENCES item(id),
    jumlah      INTEGER NOT NULL,
    catatan     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SEED DATA (skip if already exists)
INSERT INTO item VALUES
('I01','Cable Ties / Tag Koper',0,'returnable'),
('I02','Signage Kmr Mandi Gereja',0,'returnable'),
('I03','Kantong Plastik 35x55',0,'consumable'),
('I04','Handuk',0,'returnable'),
('I05','Keset',0,'returnable'),
('I06','Ziplock Anti-Bau Sepatu',0,'consumable'),
('I07','Pulpen',0,'returnable'),
('I08','Signage Kelompok 1-60',0,'returnable'),
('I09','Kertas Print Kamar',0,'consumable'),
('I10','Tom & Jerry (Laundry)',0,'returnable'),
('I11','Spidol',0,'returnable'),
('I12','Sarung Tangan Karet',0,'consumable'),
('I13','Silica Gel',0,'consumable'),
('I14','Hanger Baju',0,'returnable'),
('I15','Sticker Stager / HT',0,'consumable'),
('I16','Kantong Plastik Besar',0,'consumable'),
('I17','Selimut',0,'returnable'),
('I18','Matras',0,'returnable'),
('I19','Sprei',0,'returnable')
ON CONFLICT (id) DO NOTHING;

INSERT INTO lantai VALUES
('L01','Gereja Lt 1'),('L02','Gereja Lt 2'),('L03','Gereja Lt 3'),
('L04','Tower Lt 1'),('L05','Tower Lt 2'),('L06','Tower Lt 3'),
('L07','Tower Lt 4'),('L08','Tower Lt 5'),('L09','Tower Lt 6'),
('L10','Tower Lt 7'),('L11','Tower Lt 8'),('L12','Tower Lt 9'),
('L13','Tower Lt 10'),('L14','Tower Lt 11'),('L15','Tower Lt 12'),
('L16','Tower Lt 13'),('L17','Tower Lt 14'),('L18','Tower Lt 17'),
('L19','Tower Lt 18'),('L20','Tower Lt 19'),('L21','Tower Lt 20')
ON CONFLICT (id) DO NOTHING;

INSERT INTO sesi VALUES
('SS01','05.45','Bangun + Membangunkan Peserta'),
('SS02','06.00','Pendaftaran + Snack'),
('SS03','06.15','Briefing Akom'),
('SS04','06.30','Mandi + Makan Pagi'),
('SS05','06.45','Serah Terima Peserta dari Traffic'),
('SS06','07.00','Stand By Lantai'),
('SS07','08.00','Sesi 7 / Cleaning BM'),
('SS08','08.45','Sesi 8'),
('SS09','09.00','Pendaftaran Pindah Lobby AJC'),
('SS10','09.15','Sesi 9'),
('SS11','09.30','Drama'),
('SS12','09.45','Snack'),
('SS13','10.00','Sesi Pembuka / Foto Bersama'),
('SS14','10.15','Sesi 16 / Q&A'),
('SS15','10.30','Sesi 1 / Sesi 10'),
('SS16','11.00','Briefing Lobby Kapel Agape'),
('SS17','11.15','Sesi 2 / Sesi 11 / Sesi Penutup'),
('SS18','11.45','Makan Siang'),
('SS19','12.15','Makan Siang + Penjemputan'),
('SS20','12.45','Sesi 3 / Sesi 12'),
('SS21','13.15','Sesi 4 / Edukasi Tatib + ASJ'),
('SS22','13.45','Persiapan Museum'),
('SS23','13.45','Pengumuman + Toilet Break'),
('SS24','14.00','Sesi 5'),
('SS25','14.45','Edukasi Tatib + Pengumuman'),
('SS26','15.00','Snack / Perjalanan ke Sophilia'),
('SS27','15.30','Drama / Aktivitas / Kunjungan Museum'),
('SS28','16.00','Pengenalan Tokoh (1)'),
('SS29','16.15','Refleksi (1)'),
('SS30','16.30','Aktivitas (1) / Kunjungan Museum'),
('SS31','17.00','Pengenalan Tokoh (2)'),
('SS32','17.15','Refleksi (2)'),
('SS33','17.30','Mandi + Makan Malam'),
('SS34','19.00','Sesi 6 / Sesi 13'),
('SS35','19.15','Sesi Pak Tong'),
('SS36','19.45','Akom Naik ke Lantai'),
('SS37','20.00','Pengumuman + Istirahat (Snack Malam)'),
('SS38','20.15','Tidur'),
('SS39','21.30','Meeting Koordinasi'),
('SS40','22.30','Tidur (Panitia)')
ON CONFLICT (id) DO NOTHING;
