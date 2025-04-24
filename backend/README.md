# Subtrack - Aplikasi Pelacak Langganan dan Tagihan Otomatis

![Subtrack Logo](https://via.placeholder.com/150?text=Subtrack)

## Deskripsi

Subtrack adalah aplikasi pelacak langganan dan tagihan otomatis yang dirancang untuk membantu pengguna mengelola semua langganan digital maupun fisik mereka (seperti Netflix, Spotify, domain, hosting, dll). Aplikasi ini memudahkan pengguna untuk melacak total pengeluaran bulanan, menerima pengingat sebelum tanggal jatuh tempo, dan menganalisis pola pengeluaran berdasarkan kategori.

## Fitur Utama

- **Manajemen Langganan**
  - Tambah, edit, dan hapus langganan
  - Kategorisasi langganan (hiburan, produktivitas, utilitas, dll)
  - Dukungan untuk berbagai jenis siklus penagihan (bulanan, tahunan, kuartalan)

- **Laporan Keuangan**
  - Ringkasan total pengeluaran bulanan dan tahunan
  - Grafik analisis pengeluaran berdasarkan kategori
  - Proyeksi pengeluaran di masa depan

- **Sistem Notifikasi**
  - Pengingat sebelum tanggal jatuh tempo
  - Notifikasi email dan/atau push
  - Opsi pengaturan periode pengingat

- **Ekspor Data**
  - Ekspor laporan ke PDF untuk keperluan akuntansi
  - Ekspor data lengkap ke Excel/CSV

- **Fitur Lanjutan** (untuk pengembangan masa depan)
  - Parsing otomatis email/invoice
  - Integrasi dengan layanan perbankan
  - Rekomendasi pengoptimalan langganan

## Teknologi

- **Backend**: FastAPI (Python)
- **Database**: SQLite (MVP) / PostgreSQL (Production)
- **Frontend**: Placeholder untuk React/Mobile App di masa depan

## Panduan Instalasi

### Prasyarat

- Python 3.8+
- pip (package manager Python)
- Virtualenv (opsional tapi direkomendasikan)

### Langkah Instalasi

1. Clone repositori ini
   ```bash
   git clone https://github.com/username/subtrack.git
   cd subtrack
   ```

2. Buat dan aktifkan virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk Unix/MacOS
   # ATAU
   venv\Scripts\activate     # Untuk Windows
   ```

3. Instal dependensi
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Salin file .env.example menjadi .env dan sesuaikan konfigurasi
   ```bash
   cp .env.example .env
   # Edit file .env sesuai kebutuhan
   ```

5. Inisialisasi database
   ```bash
   alembic upgrade head
   ```

6. Jalankan server
   ```bash
   uvicorn app.main:app --reload
   ```

7. Akses API dokumentasi di browser
   ```
   http://localhost:8000/docs
   ```

## Struktur Database

Struktur database meliputi tabel-tabel utama berikut:
- Users: Menyimpan data pengguna
- Subscriptions: Menyimpan detail langganan
- Categories: Kategori untuk mengelompokkan langganan
- Notifications: Riwayat dan pengaturan notifikasi

## API Endpoints

Beberapa API endpoint utama:

- `GET /api/subscriptions` - Mendapatkan semua langganan
- `POST /api/subscriptions` - Menambahkan langganan baru
- `GET /api/subscriptions/{id}` - Mendapatkan detail langganan
- `PUT /api/subscriptions/{id}` - Memperbarui langganan
- `DELETE /api/subscriptions/{id}` - Menghapus langganan
- `GET /api/reports/monthly` - Mendapatkan laporan bulanan
- `GET /api/notifications` - Mendapatkan pengingat langganan

## Ide Monetisasi

1. **Model Freemium**:
   - Gratis: Manajemen hingga 5 langganan, notifikasi email
   - Premium: Langganan tak terbatas, notifikasi push, ekspor data, analisis lanjutan

2. **White-label Solution**:
   - Menawarkan versi white-label untuk bank dan lembaga keuangan

3. **Marketplace Integrasi**:
   - Komisi dari penawaran khusus atau diskon untuk pengguna yang berlangganan melalui aplikasi

4. **API as a Service**:
   - Menyediakan API untuk integrasi dengan aplikasi keuangan lainnya

## Pengembangan Lebih Lanjut

- Aplikasi mobile (Android & iOS)
- Browser extension untuk otomatisasi deteksi langganan
- Integrasi dengan layanan perbankan untuk deteksi otomatis langganan
- Rekomendasi penghematan berdasarkan AI
- Integrasi dengan layanan pembayaran untuk manajemen langganan langsung dari aplikasi

## Kontribusi

Kontribusi selalu diterima dengan baik! Silakan buat issue atau pull request untuk perbaikan atau penambahan fitur.

## Lisensi

[MIT License](LICENSE)