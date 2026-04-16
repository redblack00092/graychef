.PHONY: backend frontend

backend:
	cd backend && \
	python3 -m venv .venv && \
	.venv/bin/pip install -q -r requirements.txt && \
	.venv/bin/uvicorn main:app --reload --port 8000

frontend:
	cd frontend && npm install && npm run dev
