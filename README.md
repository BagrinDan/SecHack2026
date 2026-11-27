# MuleTrace MD

Прототип системы отслеживания счетов-мулов в платёжной сети MIA (Молдова).
Только синтетические Zero-PII данные: счета — токены (12 символов SHA-256), без ФИО/IDNP/IBAN.

Порядок разработки: [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md).

## Запуск бэкенда

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- WebSocket: `ws://localhost:8000/ws/transactions`
