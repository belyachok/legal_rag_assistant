Что установить
Python 3.10 или 3.11 — https://www.python.org/downloads/
(при установке отметить "Add Python to PATH")

Tesseract OCR — https://github.com/UB-Mannheim/tesseract/wiki
(скачать tesseract-ocr-w64-setup-5.3.3.20231005.exe, установить, запомнить путь)

Node.js — https://nodejs.org/ (LTS версия)
(после установки перезагрузить компьютер)

Как запустить
Бэкенд
Открыть терминал PowerShell:

cd E:\wizard\интеллектуальный помощник\legal_rag_assistant\backend
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

Фронтенд (открыть НОВЫЙ терминал)

cd E:\wizard\интеллектуальный помощник\legal_rag_assistant\frontend
npm install
npm start