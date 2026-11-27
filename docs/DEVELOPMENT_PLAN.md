# План коммитов: MuleTrace MD

> **Это основной документ разработки.** Вся работа над проектом ведётся строго по этому плану:
> коммит за коммитом, в указанном порядке, с проверкой DoD перед переходом к следующему шагу.
> Фокус команды — **бэкенд и API** (этапы 1–2 и бэкенд-часть этапа 4).

Последовательный пошаговый план разработки MVP системы отслеживания счетов-мулов в сети MIA с интеграцией для maib.

- **Формат сообщений:** [Conventional Commits](https://www.conventionalcommits.org/).
- **Стратегия ветвления:** работа в `main` с атомарными коммитами после каждой рабочей фичи (либо 2 ветки: `feat/backend` и `feat/frontend` с последующим мёржем перед полировкой).

---

## Архитектура MVP

- **Слой симуляции MIA:** генератор потока мгновенных платежей между 5 банками Молдовы (`maib`, `MICB`, `Victoriabank`, `OTP Bank`, `FinComBank`) в MDL с подмешиванием реальных паттернов отмывания.
- **Графовый движок трассировки (Trace Engine):** строит направленный мультиграф транзакций в памяти, вычисляет деревья распределения (Dispersion Trees), время удержания средств (Dwell Time), поколения мулов (1–4+) и циклические переводы.
- **API-шлюз для maib:** минимальная интеграция — два эндпоинта: `POST /api/trace` (банк сообщает о жалобе клиента на мошенничество) и поток `GET /api/alerts` (система возвращает подозрительные счета внутри базы maib и смежных банков).
- **Дашборд аналитика:** визуализация дерева распределения с цветовой кодировкой молдавских банков (аналог схемы из отчёта Mastercard), очередь алертов и панель запуска демо-сценариев для жюри.

> ⚠️ **Открытый вопрос:** в архитектуре трассировка — `POST /api/trace` (жалоба от банка), а в Commit 7 — `GET /api/trace/{tx_id}`.
> Рабочее решение: в Commit 7 реализовать оба (`POST` принимает жалобу и возвращает дерево, `GET` — повторное чтение по `tx_id`).

---

## Этап 1. Каркас проекта и симулятор MIA

### Commit 1 — `chore: init project structure and backend dependencies`
- [x] **Файлы:** `.gitignore`, `README.md`, `backend/requirements.txt`
- **Что делаем:**
  - Инициализируем git-репозиторий, создаём директории `/backend` и `/frontend`.
  - Добавляем в `backend/requirements.txt`: `fastapi`, `uvicorn[standard]`, `networkx`, `pydantic`, `websockets`.
  - Настраиваем `.gitignore` (Python `venv/`, `__pycache__/`, `node_modules/`, `.env`).
- **Проверка (DoD):** виртуальное окружение создано, `pip install -r backend/requirements.txt` проходит без ошибок.

### Commit 2 — `feat(models): add Zero-PII data schemas and bank registry`
- [x] **Файлы:** `backend/models.py`
- **Что делаем:**
  - Описываем Pydantic-модели: `BankCode` (MAIB, MICB, VICTORIABANK, OTP, FINCOMBANK), `AccountType` (PERSONAL, BUSINESS), `AccountStatus` (ACTIVE, SUSPECT, FROZEN).
  - Добавляем утилиту генерации Zero-PII токена (SHA-256 с солью, первые 12 символов) вместо реальных IBAN/IDNP.
  - Описываем схемы `Account`, `Transaction`, `MuleAlert`, `DispersionGraph`.
- **Проверка (DoD):** модуль импортируется без ошибок, тестовая генерация модели в Python REPL работает.

### Commit 3 — `feat(simulator): implement MIA background traffic and 3 fraud injectors`
- [x] **Файлы:** `backend/simulator.py`
- **Что делаем:**
  - Реализуем пул синтетических токенизированных счетов по 5 банкам Молдовы.
  - Пишем асинхронный генератор фонового легитимного трафика (1–2 транзакции/сек, суммы 50–3500 MDL).
  - Пишем 3 функции-инъектора для демо:
    - `inject_layered_mule_chain()` — кража 48 000 MDL из MAIB и дробление до 4-го поколения.
    - `inject_business_mule_ring()` — аномальный приток на бизнес-счёт в MAIB с быстрым выводом.
    - `inject_test_and_cycle()` — тестовый микроперевод 15 MDL + прогон 35 000 MDL по кольцу.
- **Проверка (DoD):** локальный скрипт-прогон генерирует валидные цепочки транзакций с корректными временными метками.

### Commit 4 — `feat(ws): setup FastAPI app with in-memory graph and live MIA WebSocket`
- [x] **Файлы:** `backend/main.py`
- **Что делаем:**
  - Поднимаем FastAPI с CORS (`allow_origins=["*"]`).
  - Инициализируем NetworkX `MultiDiGraph` в памяти и фоновую задачу симулятора при старте (lifespan).
  - Реализуем WebSocket-эндпоинт `/ws/transactions` для стриминга потока транзакций на фронтенд.
- **Проверка (DoD):** сервер запускается через `uvicorn main:app --reload`, подключение к `ws://localhost:8000/ws/transactions` выдаёт JSON-транзакции в реальном времени.

## Этап 2. Графовый движок трассировки и API

### Commit 5 — `feat(engine): add temporal BFS tracing and Dispersion Tree builder`
- [x] **Файлы:** `backend/graph_engine.py`
- **Что делаем:**
  - Реализуем метод `trace_funds(start_tx_id, max_depth=5)`: обход графа вперёд строго по возрастанию времени (в пределах 24-часового окна).
  - Рассчитываем для каждого узла: поколение мула (`generation`), суммы `total_in` / `total_out` и время удержания средств (`dwell_time_sec`).
  - Форматируем ответ в структуру `nodes` + `edges`, готовую для отрисовки в React Flow.
- **Проверка (DoD):** при вызове трассировки на корневой транзакции сценария layered возвращается дерево глубиной до 4 поколений.

### Commit 6 — `feat(alerts): implement rule-based mule scoring and pattern detection`
- [x] **Файлы:** `backend/graph_engine.py`
- **Что делаем:**
  - Добавляем автоматический пересчёт `risk_score` (0–100) при поступлении транзакций по 5 правилам:
    | Правило | Условие | Баллы |
    |---|---|---|
    | Rapid Hop | Dwell Time < 10 мин | +35 |
    | Smurfing / Fan-Out | дробление на 3+ счёта | +30 |
    | Cycling | замкнутый цикл длиной 3–5 узлов | +40 |
    | Test Transaction | < 50 MDL перед крупным переводом > 10 000 MDL | +25 |
    | Multi-tree Reuse | появление в нескольких деревьях | +30 |
  - При достижении порога `risk_score >= 60` формируем `MuleAlert` с перечнем сработавших правил.
- **Проверка (DoD):** запуск любого из 3 сценариев автоматически создаёт релевантные алерты с заполненными тегами правил.

### Commit 7 — `feat(api): expose REST endpoints for simulation, trace, alerts, freeze, and KPI`
- [x] **Файлы:** `backend/main.py`
- **Что делаем:** добавляем эндпоинты:
  - `POST /api/simulate/{scenario}` (`layered` | `business` | `cycle`)
  - `GET /api/trace/{tx_id}`
  - `GET /api/alerts?bank=MAIB`
  - `POST /api/accounts/{account_hash}/freeze`
  - `GET /api/kpi` (объём транзакций, количество мулов, средний dwell_time, сумма в MDL, endpoint_hotlist)
- **Проверка (DoD):** все эндпоинты протестированы через Swagger UI (`/docs`) и возвращают код `200 OK`.

## Этап 3. Фронтенд-дашборд аналитика maib

### Commit 8 — `chore(frontend): bootstrap React + Vite + Tailwind + React Flow`
- [x] **Файлы:** `frontend/package.json`, `frontend/tailwind.config.js`, `frontend/src/index.css`, `frontend/src/api.js`
- **Что делаем:**
  - Разворачиваем шаблон Vite (React), устанавливаем `tailwindcss`, `reactflow`, `lucide-react`.
  - Настраиваем тёмную тему SOC (`#0B0F19`) и константы цветов молдавских банков (MAIB, MICB, VICTORIABANK, OTP, FINCOMBANK).
  - Выносим вызовы REST API и URL WebSocket в `src/api.js`.
- **Проверка (DoD):** `npm run dev` открывает пустой тёмный экран без ошибок в консоли.

### Commit 9 — `feat(ui): build header, real-time KPI bar, and Attack Simulator buttons`
- [x] **Файлы:** `frontend/src/components/Header.jsx`, `frontend/src/components/KpiBar.jsx`, `frontend/src/App.jsx`
- **Что делаем:**
  - Верстаем верхнюю панель «MuleTrace MD | MIA Network Intelligence».
  - Подключаем автообновление 4 KPI-карточек (интервал 2–3 сек).
  - Добавляем 3 кнопки запуска демо-сценариев, которые дёргают `POST /api/simulate/{scenario}` и передают полученный `root_tx_id` в стейт графа.
- **Проверка (DoD):** клик по кнопке атаки запускает симуляцию на бэкенде, счётчики KPI растут.

### Commit 10 — `feat(graph): implement interactive Dispersion Tree with React Flow`
- [x] **Файлы:** `frontend/src/components/DispersionGraph.jsx`, `frontend/src/components/MuleNode.jsx`
- **Что делаем:**
  - Создаём кастомный узел `MuleNode`: цветная полоска банка, короткий хэш, бейдж Risk Score, поколение мула, Dwell Time, статус FROZEN (красная рамка + иконка замка).
  - Реализуем раскладку слева направо по координате `X = generation * 280` (чтобы не тратить время на тяжёлые графовые движки).
  - Настраиваем анимированные рёбра: толщина линии пропорциональна `amount_mdl`, тестовые переводы — пунктиром, подпись суммы в MDL.
- **Проверка (DoD):** после клика по любой из 3 кнопок атаки граф красиво и читаемо отрисовывается без наложения узлов.

### Commit 11 — `feat(compliance): add alert queue, account freeze modal, and live MIA feed`
- [x] **Файлы:** `frontend/src/components/AlertQueue.jsx`, `frontend/src/components/LiveFeed.jsx`, `frontend/src/components/NodeDetailsDrawer.jsx`
- **Что делаем:**
  - Добавляем правую панель «Очередь алертов» с фильтром «Все банки MIA / Только клиенты maib» и кнопками «Трассировать» / «Заморозить».
  - При клике на узел графа открываем карточку с деталями и кнопкой блокировки (`POST /api/accounts/{hash}/freeze`).
  - В нижней части экрана подключаем WebSocket-ленту живых токенизированных транзакций MIA.
- **Проверка (DoD):** полный сквозной цикл работает — атака → алерт → трассировка → клик по узлу → заморозка.

## Этап 4. Полировка для презентации и запуск

### Commit 12 — `feat(demo): add demo reset, Endpoint Hotlist analytics, and freeze feedback`
- [ ] **Файлы:** `backend/main.py`, `frontend/src/components/HotlistPanel.jsx`, `frontend/src/components/DispersionGraph.jsx`
- **Что делаем:**
  - Добавляем `POST /api/reset` и кнопку «Сбросить демо» в интерфейс для чистого перезапуска перед менторами.
  - Добавляем вкладку «Аналитика сети (Hotlist)» с топ-5 точками вывода средств и распределением мулов по банкам.
  - При заморозке узла перекрашиваем исходящие от него рёбра в серый пунктир и показываем тост: «Сигнал блокировки отправлен в [BANK] за 45 мс. Предотвращён вывод X MDL».
- **Проверка (DoD):** повторный прогон всех 3 сценариев через «Сбросить демо» проходит стабильно и без утечек состояния.

### Commit 13 — `docs: add one-command start script and pitch demo runbook`
- [ ] **Файлы:** `start_demo.sh`, `README.md`
- **Что делаем:**
  - Пишем скрипт `start_demo.sh` для одновременного запуска FastAPI и Vite.
  - Фиксируем в `README.md` короткий чеклист действий для живой демонстрации перед жюри (какие кнопки нажимать и на какие метрики обращать внимание).
- **Проверка (DoD):** проект полностью поднимается одной командой с чистого терминала.

---

## Финальная подготовка к защите
- **Code Freeze** — после завершения Commit 13 в код вносятся только критические хотфиксы (`fix:`).
- Репетиция питча и проверка работы демо при отключённом интернете (всё работает локально на `localhost`).
