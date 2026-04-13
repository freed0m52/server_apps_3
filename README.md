# FastAPI Server Application - Контрольная работа №3

## Описание проекта

Серверное приложение на FastAPI с реализацией полного спектра функций безопасности и работы с данными:

-  Аутентификация и авторизация (RBAC)
-  JWT токены с расширенной защитой
-  Rate limiting для защиты от злоупотреблений
-  CRUD операции с базой данных SQLite
-  Динамическая документация в зависимости от режима окружения

### Выполненные задания

| Задание | Описание |
|---------|----------|
| 6.2 | Basic аутентификация с хешированием паролей (bcrypt)
| 6.3 | Управление документацией в зависимости от режима окружения 
| 6.4 | JWT аутентификация 
| 6.5 | Расширенная JWT аутентификация + Rate Limiting
| 7.1 | RBAC с ролями admin/user/guest 
| 8.1 | SQLite + регистрация пользователей 
| 8.2 | Полные CRUD операции для Todo

## Требования

- Python 3.8 или выше
- pip (менеджер пакетов Python)

## Установка и запуск
### 2️⃣ Создание виртуального окружения
```bash
python -m venv venv
venv\Scripts\activate
```
### 3️⃣ Установка зависимостей
```bash
pip install -r requirements.txt
```
### 4️⃣ Настройка окружения
Скопируйте файл .env.example в .env:
```bash
copy .env.example .env
```
### 5️⃣ Инициализация базы данных
```bash
python init_db.py
```
### 6️⃣ Запуск приложения
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
## 👥 Тестовые пользователи

| Пользователь | Пароль | Роль |
|--------------|--------|------|
| admin | adminpass | admin |
| testuser | testpass | user |
| guestuser | guestpass | guest |

## 🔧 Команды для тестирования через curl

### 👤 Регистрация и аутентификация

# Регистрация нового пользователя
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"artem","password":"qwerty123"}'
```
# GET логин с Basic Auth
```bash
curl -u artem:qwerty123 http://localhost:8000/login
```
# POST логин для получения JWT токена
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"artem","password":"qwerty123"}'
```

### Доступ к защищенным ресурсам

# Доступ к защищенному ресурсу с JWT токеном
```bash
curl -X GET http://localhost:8000/protected_resource \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```
# Доступ к admin ресурсу
# Сначала получите токен для admin
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpass"}'
```
# Затем используйте полученный токен
```bash
curl -X GET http://localhost:8000/admin/resource \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 💾 Работа с SQLite и Todo

# Регистрация в SQLite
```bash
curl -X POST http://localhost:8000/register-sqlite \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"bob123"}'
```
# Создание Todo
```bash
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk","description":"Get 2 liters"}'
```
# Получение Todo по ID
```bash
curl -X GET http://localhost:8000/todos/1
```
# Обновление Todo
```bash
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy eggs","description":"Get 12 eggs","completed":true}'
```
# Удаление Todo
```bash
curl -X DELETE http://localhost:8000/todos/1
```

## 📁 Структура проекта

```
.env.example        # Пример конфигурации окружения
.gitignore          # Игнорируемые файлы
README.md           # Документация
requirements.txt    # Зависимости Python
main.py             # Главный файл приложения
auth.py             # Аутентификация и JWT
database.py         # Работа с SQLite
models.py           # Pydantic модели
rbac.py             # Управление ролями
rate_limiter.py     # Ограничение запросов
init_db.py          # Инициализация базы данных
todos.db            # База данных SQLite
```

## ⚙️ Конфигурация окружения

Файл .env должен содержать следующие переменные:

```
**env**
MODE=DEV
DOCS_USER=admin
DOCS_PASSWORD=secret123
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
```

**⚠️ Важно**: Никогда не публикуйте реальные секреты в репозитории!

## 📊 Ожидаемые ответы API

### Успешные ответы

| Операция | Статус | Ответ |
|----------|--------|-------|
| Регистрация | 201 | **\`{"message":"New user created"}\`** |
| JWT логин | 200 | **\`{"access_token":"...","token_type":"bearer"}\`** |
| Доступ к ресурсу | 200 | **\`{"message":"Access granted"}\`** |
| Создание Todo | 201 | **\`{"id":1,"title":"...","description":"...","completed":false}\`** |

### Ошибки

| Ошибка | Статус | Описание |
|--------|--------|----------|
| Пользователь существует | 409 | Conflict |
| Неверные учетные данные | 401 | Unauthorized |
| Недостаточно прав | 403 | Forbidden |
| Не найдено | 404 | Not Found |
| Превышение лимита запросов | 429 | Too Many Requests |

## 🛡️ Безопасность

- **Хеширование паролей**: bcrypt
- **Защита от тайминг-атак**: secrets.compare_digest()
- **Rate limiting**:
  - **\`/register\`** - 1 запрос в минуту
  - **\`/login\`** - 5 запросов в минуту
- **JWT токены**: истекают через 30 минут

## 🛠️ Используемые технологии

| Технология | Назначение |
|------------|------------|
| FastAPI | Веб-фреймворк |
| SQLite | База данных |
| PyJWT | JWT токены |
| PassLib + bcrypt | Хеширование паролей |
| SlowAPI | Rate limiting |
| Python-dotenv | Управление переменными окружения |

## 🔧 Устранение неполадок

### Проблема с bcrypt

Если возникает ошибка **\`module 'bcrypt' has no attribute '__about__'\`**:

**\`\`\`bash**
pip uninstall bcrypt passlib -y
pip install bcrypt==4.0.1 passlib==1.7.4
**\`\`\`**

### Порт уже используется

**\`\`\`bash**
uvicorn main:app --reload --port 8001
**\`\`\`**

### Проблемы с правами в PowerShell

**\`\`\`powershell**
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
**\`\`\`**

### Проверка работоспособности

Если возникают проблемы, проверьте:

- **✅** Запущен ли сервер (**\`uvicorn main:app --reload\`**)
- **✅** Правильно ли настроен файл **\`.env\`**
- **✅** Создана ли база данных (**\`python init_db.py\`**)
