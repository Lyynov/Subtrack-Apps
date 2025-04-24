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
  - Ekspor laporan ke PDF untuk keperluan akuntansi

- **Sistem Notifikasi**
  - Pengingat sebelum tanggal jatuh tempo
  - Notifikasi email dan/atau push
  - Opsi pengaturan periode pengingat

- **Fitur Lanjutan**
  - Parsing otomatis email/invoice untuk deteksi langganan
  - Riwayat pembayaran
  - Laporan tren pengeluaran

## Tech Stack

- **Backend**: FastAPI (Python 3.9+)
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **ORM**: SQLAlchemy
- **Migrasi DB**: Alembic
- **Otentikasi**: JWT (JSON Web Tokens)
- **Containerization**: Docker

## Struktur Proyek

```
subtrack/
├── backend/                 # Backend API
│   ├── alembic/             # Migrasi database
│   ├── app/                 # Kode aplikasi utama
│   │   ├── api/             # API endpoints
│   │   ├── auth/            # Autentikasi
│   │   ├── db/              # Model dan konfigurasi database
│   │   ├── schemas/         # Pydantic schemas untuk validasi
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Fungsi-fungsi utilitas
│   │   ├── config.py        # Konfigurasi aplikasi
│   │   └── main.py          # Entry point aplikasi
│   ├── logs/                # Log aplikasi
│   ├── mock_data/           # Data sampel untuk development
│   ├── scripts/             # Scripts utilitas
│   ├── static/              # File statis (gambar, logo, dll)
│   ├── tests/               # Unit dan integrasi tests
│   ├── .env.example         # Template untuk file konfigurasi
│   ├── Dockerfile           # Konfigurasi Docker
│   └── requirements.txt     # Dependensi Python
├── frontend/                # Placeholder untuk frontend
├── docker-compose.yml       # Konfigurasi Docker Compose
├── Makefile                 # Shortcuts untuk perintah umum
└── README.md                # Dokumentasi proyek
```

## Panduan Instalasi

### Prasyarat

- [Docker](https://www.docker.com/get-started) dan [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.9+](https://www.python.org/downloads/) (jika ingin menjalankan tanpa Docker)
- [Git](https://git-scm.com/downloads)

### Menggunakan Docker

1. Clone repositori ini
   ```bash
   git clone https://github.com/username/subtrack.git
   cd subtrack
   ```

2. Salin file konfigurasi lingkungan
   ```bash
   cp backend/.env.example backend/.env
   ```

3. Edit file `.env` dan sesuaikan konfigurasi seperti `SECRET_KEY` dan pengaturan database

4. Jalankan dengan Docker Compose
   ```bash
   docker-compose up -d
   ```

5. Inisialisasi database
   ```bash
   docker exec -it subtrack-backend alembic upgrade head
   ```

6. (Opsional) Muat data contoh untuk pengujian
   ```bash
   docker exec -it subtrack-backend python scripts/load_mock_data.py --mock-data
   ```

7. Akses API di browser
   ```
   http://localhost:8000/docs
   ```

### Menjalankan Secara Lokal (Tanpa Docker)

1. Clone repositori ini
   ```bash
   git clone https://github.com/username/subtrack.git
   cd subtrack
   ```

2. Buat dan aktifkan virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # atau
   venv\Scripts\activate     # Windows
   ```

3. Instal dependensi
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Salin dan konfigurasi file .env
   ```bash
   cp .env.example .env
   # Edit file .env sesuai kebutuhan
   ```

5. Inisialisasi database
   ```bash
   alembic upgrade head
   ```

6. Jalankan aplikasi
   ```bash
   uvicorn app.main:app --reload
   ```

7. Akses API di browser
   ```
   http://localhost:8000/docs
   ```

## Database Schema

```
+------------------+       +------------------+       +------------------+
|      Users       |       |    Categories    |       |  Subscriptions   |
+------------------+       +------------------+       +------------------+
| id               |       | id               |       | id               |
| email            |       | name             |       | name             |
| hashed_password  |       | description      |       | description      |
| full_name        |       | color            |       | amount           |
| is_active        |       | user_id          |       | currency         |
| role             |       | created_at       |       | billing_cycle    |
| created_at       |       +------------------+       | billing_day      |
| updated_at       |                |                 | next_billing_date|
+------------------+                |                 | start_date       |
        |                           |                 | end_date         |
        |                           |                 | auto_renew       |
        |                           |                 | reminder_days    |
        |                           |                 | website_url      |
        |                           |                 | notes            |
        |                           |                 | is_active        |
        |                           |                 | user_id          |
        |                           +---------------->| category_id      |
        |                                             | created_at       |
        |                                             | updated_at       |
        |                                             +------------------+
        |                                                     |
        |                                                     |
        |                                                     v
        |                 +------------------+       +------------------+
        |                 |  Notifications   |       | Payment_History  |
        |                 +------------------+       +------------------+
        |                 | id               |       | id               |
        |                 | user_id          |       | subscription_id  |
        +---------------->| subscription_id  |       | payment_date     |
                          | type             |       | amount           |
                          | subject          |       | status           |
                          | message          |       | payment_method   |
                          | status           |       | receipt_url      |
                          | scheduled_at     |       | notes            |
                          | sent_at          |       | created_at       |
                          | read_at          |       +------------------+
                          | created_at       |
                          +------------------+
```

## API Endpoints

### Autentikasi

- `POST /api/auth/token` - Mendapatkan JWT access token

### Pengguna

- `POST /api/users/` - Membuat pengguna baru
- `GET /api/users/` - Mendapatkan daftar pengguna
- `GET /api/users/{user_id}` - Mendapatkan detail pengguna
- `PUT /api/users/{user_id}` - Memperbarui pengguna
- `DELETE /api/users/{user_id}` - Menghapus pengguna

### Kategori

- `POST /api/categories/` - Membuat kategori baru
- `GET /api/categories/` - Mendapatkan daftar kategori
- `GET /api/categories/with-count` - Mendapatkan daftar kategori dengan jumlah langganan
- `GET /api/categories/{category_id}` - Mendapatkan detail kategori
- `PUT /api/categories/{category_id}` - Memperbarui kategori
- `DELETE /api/categories/{category_id}` - Menghapus kategori

### Langganan

- `POST /api/subscriptions/` - Membuat langganan baru
- `GET /api/subscriptions/` - Mendapatkan daftar langganan
- `GET /api/subscriptions/summary` - Mendapatkan ringkasan langganan
- `GET /api/subscriptions/{subscription_id}` - Mendapatkan detail langganan
- `PUT /api/subscriptions/{subscription_id}` - Memperbarui langganan
- `DELETE /api/subscriptions/{subscription_id}` - Menghapus langganan

### Pembayaran

- `POST /api/payments/` - Mencatat pembayaran baru
- `GET /api/payments/` - Mendapatkan riwayat pembayaran
- `GET /api/payments/subscription/{subscription_id}` - Mendapatkan pembayaran untuk langganan tertentu
- `GET /api/payments/{payment_id}` - Mendapatkan detail pembayaran
- `PUT /api/payments/{payment_id}` - Memperbarui data pembayaran
- `DELETE /api/payments/{payment_id}` - Menghapus data pembayaran
- `POST /api/payments/record/{subscription_id}` - Mencatat pembayaran untuk langganan tertentu

### Notifikasi

- `POST /api/notifications/` - Membuat notifikasi baru
- `GET /api/notifications/` - Mendapatkan daftar notifikasi
- `GET /api/notifications/{notification_id}` - Mendapatkan detail notifikasi
- `PUT /api/notifications/{notification_id}` - Memperbarui notifikasi
- `DELETE /api/notifications/{notification_id}` - Menghapus notifikasi
- `POST /api/notifications/{notification_id}/read` - Menandai notifikasi sebagai telah dibaca
- `POST /api/notifications/upcoming-reminders` - Membuat pengingat untuk langganan yang akan datang

### Laporan

- `GET /api/reports/monthly/{year}/{month}` - Mendapatkan laporan bulanan
- `GET /api/reports/yearly/{year}` - Mendapatkan laporan tahunan
- `GET /api/reports/payments` - Mendapatkan laporan riwayat pembayaran
- `GET /api/reports/trends` - Mendapatkan laporan tren langganan
- `GET /api/reports/export/monthly/{year}/{month}` - Mengekspor laporan bulanan (PDF/Excel)
- `GET /api/reports/export/yearly/{year}` - Mengekspor laporan tahunan (PDF/Excel)

## Utilitas dan Fitur Khusus

### Email Parser

Subtrack memiliki fitur email parser yang dapat mengekstrak informasi langganan dari email. Parser ini dapat:

- Mengidentifikasi layanan berlangganan berdasarkan pola dalam email
- Mengekstrak informasi harga/biaya
- Mengekstrak tanggal penagihan
- Otomatis membuat entri langganan di sistem

Untuk menggunakan fitur ini, Anda perlu mengonfigurasi pengaturan IMAP di file `.env`:

```
IMAP_SERVER=imap.example.com
IMAP_PORT=993
IMAP_USERNAME=your-email@example.com
IMAP_PASSWORD=your-email-password
IMAP_USE_SSL=true
```

### PDF Generator

Subtrack dapat menghasilkan laporan PDF yang terformat dengan rapi, termasuk:

- Laporan bulanan dengan ringkasan pengeluaran
- Laporan tahunan dengan analisis tren
- Detail langganan dengan riwayat pembayaran
- Visualisasi data seperti grafik lingkaran, batang, dan garis

### Penjadwal Notifikasi

Sistem penjadwal notifikasi berjalan sebagai layanan terpisah yang:

- Secara otomatis membuat pengingat untuk langganan yang akan jatuh tempo
- Mengirim notifikasi email pada waktu yang ditentukan
- Memantau status notifikasi dan mencatat ketika notifikasi telah dikirim

Untuk menjalankan penjadwal notifikasi:

```bash
# Dengan Docker (sudah termasuk dalam docker-compose.yml)
# Tanpa Docker
python backend/scripts/notification_scheduler.py
```

## Pengembangan

### Menjalankan Tests

```bash
# Dengan Docker
docker exec -it subtrack-backend pytest

# Tanpa Docker
cd backend
pytest
```

### Migrasi Database

Untuk membuat migrasi baru setelah mengubah model:

```bash
# Dengan Docker
docker exec -it subtrack-backend alembic revision --autogenerate -m "Deskripsi perubahan"

# Tanpa Docker
cd backend
alembic revision --autogenerate -m "Deskripsi perubahan"
```

Untuk menerapkan migrasi:

```bash
# Dengan Docker
docker exec -it subtrack-backend alembic upgrade head

# Tanpa Docker
cd backend
alembic upgrade head
```

## Rencana Pengembangan Masa Depan

1. **Frontend**
   - Aplikasi web berbasis React atau Vue
   - Aplikasi mobile dengan React Native atau Flutter

2. **Fitur Tambahan**
   - Integrasi dengan layanan perbankan
   - Rekomendasi pengoptimalan langganan menggunakan AI
   - Dukungan multi-bahasa
   - Tema gelap/terang

3. **Perluasan**
   - API publik untuk integrasi dengan aplikasi lain
   - Browser extension untuk deteksi langganan otomatis
   - Widget untuk dashboard OS

## Kontribusi

Kontribusi selalu diterima dengan baik! Silakan buat issue atau pull request untuk perbaikan atau penambahan fitur.

1. Fork repositori
2. Buat branch fitur Anda (`git checkout -b feature/amazing-feature`)
3. Commit perubahan Anda (`git commit -m 'Add some amazing feature'`)
4. Push ke branch (`git push origin feature/amazing-feature`)
5. Buka Pull Request

## Lisensi

Didistribusikan di bawah Lisensi MIT. Lihat `LICENSE` untuk informasi lebih lanjut.

## Kontak

Noval Fadli Robbani - [novalfadli13@gmail.com]
