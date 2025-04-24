# Subtrack Makefile
# Shortcuts untuk perintah-perintah umum

.PHONY: help setup run stop logs shell test db-init db-migrate db-upgrade init-dev format clean

# Variabel
APP_NAME = subtrack
BACKEND_CONTAINER = $(APP_NAME)-backend
DB_CONTAINER = $(APP_NAME)-postgres

help:
	@echo "Subtrack Makefile"
	@echo ""
	@echo "Perintah yang tersedia:"
	@echo "  make setup       - Menyiapkan lingkungan (variabel env, dsb)"
	@echo "  make run         - Menjalankan aplikasi dengan docker-compose"
	@echo "  make stop        - Menghentikan semua container docker"
	@echo "  make logs        - Menampilkan logs backend"
	@echo "  make shell       - Masuk ke shell backend container"
	@echo "  make test        - Menjalankan test"
	@echo "  make db-init     - Inisialisasi database"
	@echo "  make db-migrate  - Membuat migrasi database baru"
	@echo "  make db-upgrade  - Menerapkan migrasi database"
	@echo "  make load-mock   - Memuat data contoh"
	@echo "  make init-dev    - Setup lingkungan pengembangan lokal"
	@echo "  make format      - Format kode dengan black"
	@echo "  make clean       - Membersihkan file yang dihasilkan"

setup:
	@if [ ! -f ./backend/.env ]; then \
		cp ./backend/.env.example ./backend/.env; \
		echo "File .env dibuat. Silakan edit sesuai kebutuhan."; \
	else \
		echo "File .env sudah ada."; \
	fi

run:
	docker-compose up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f backend

shell:
	docker exec -it $(BACKEND_CONTAINER) bash

test:
	docker exec -it $(BACKEND_CONTAINER) pytest

db-init:
	docker exec -it $(BACKEND_CONTAINER) alembic upgrade head

db-migrate:
	@echo "Membuat migrasi baru..."
	@read -p "Masukkan deskripsi migrasi: " desc; \
	docker exec -it $(BACKEND_CONTAINER) alembic revision --autogenerate -m "$$desc"

db-upgrade:
	docker exec -it $(BACKEND_CONTAINER) alembic upgrade head

load-mock:
	docker exec -it $(BACKEND_CONTAINER) python scripts/load_mock_data.py --mock-data

init-dev:
	@echo "Mengatur lingkungan pengembangan lokal..."
	@if [ ! -d ./venv ]; then \
		python -m venv venv; \
		echo "Virtual environment dibuat."; \
	fi
	. venv/bin/activate && pip install -r backend/requirements.txt
	. venv/bin/activate && pip install black pytest-cov
	@if [ ! -f ./backend/.env ]; then \
		cp ./backend/.env.example ./backend/.env; \
		echo "File .env dibuat. Silakan edit sesuai kebutuhan."; \
	fi
	@echo "Lingkungan pengembangan siap. Gunakan 'source venv/bin/activate' untuk mengaktifkan venv."

format:
	@if [ -d ./venv ]; then \
		. venv/bin/activate && black backend/app; \
	else \
		docker exec -it $(BACKEND_CONTAINER) black /app/app; \
	fi

clean:
	@echo "Membersihkan file temporary..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "Pembersihan selesai."