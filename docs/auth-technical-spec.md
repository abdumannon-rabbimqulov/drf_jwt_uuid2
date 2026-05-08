# Auth moduli uchun texnik topshiriq

## 1. Maqsad

HeadHunterga o'xshash ish qidirish platformasi uchun birinchi bosqichda to'liq
authentifikatsiya va avtorizatsiya modulini ishlab chiqish. Modul keyingi
qismlar, masalan ish beruvchi profili, kandidat profili, vakansiyalar va
rezyumelar bilan integratsiya qilinishga tayyor bo'lishi kerak.

Loyiha backend qismi to'liq FastAPI asosida asinxron yoziladi.

## 2. Texnologiyalar

- Python 3.12+
- FastAPI
- Uvicorn yoki Granian
- SQLAlchemy 2.x async ORM
- Alembic
- PostgreSQL
- Redis
- Pydantic v2
- PyJWT yoki python-jose
- Passlib yoki pwdlib
- AioSMTP yoki tashqi email provider SDK/API
- Docker
- Docker Compose
- Pytest, pytest-asyncio, httpx
- Ruff, mypy

## 3. Auth modul chegarasi

Bu bosqichda faqat auth qismi qilinadi.

Kiritiladi:

- Ro'yxatdan o'tish
- Email orqali tasdiqlash kodi yuborish
- Email tasdiqlash
- Login
- JWT access token va refresh token
- Token refresh qilish
- Logout
- Parolni unutganda email kod yuborish
- Parolni tiklash
- Joriy foydalanuvchi ma'lumotini olish
- Parolni almashtirish
- Bazaviy role/permission tayyorlash
- Docker orqali ishga tushirish
- Testlar

Kiritilmaydi:

- Vakansiya moduli
- Rezyume moduli
- Kandidat va ish beruvchi to'liq profillari
- To'lovlar
- Chat
- Admin panelning to'liq biznes funksiyalari

## 4. Foydalanuvchi rollari

Birinchi bosqichda quyidagi rollar bo'lishi kerak:

- `candidate` - ish qidiruvchi
- `employer` - ish beruvchi
- `admin` - tizim administratori

Ro'yxatdan o'tishda foydalanuvchi `candidate` yoki `employer` rolini tanlaydi.
`admin` roli faqat seed/script yoki database orqali beriladi.

## 5. Ma'lumotlar bazasi modeli

### 5.1. users

Maydonlar:

- `id` UUID, primary key
- `email` varchar, unique, indexed, lowercase
- `password_hash` varchar
- `role` enum: `candidate`, `employer`, `admin`
- `is_active` boolean, default true
- `is_email_verified` boolean, default false
- `created_at` timestamptz
- `updated_at` timestamptz
- `last_login_at` timestamptz, nullable

Talablar:

- Email unique bo'lishi shart.
- Parol hech qachon plain text saqlanmasin.
- O'chirish uchun keyingi bosqichlarda soft delete qo'shishga joy qoldiriladi.

### 5.2. email_verification_codes

Maydonlar:

- `id` UUID, primary key
- `user_id` UUID, foreign key users.id
- `email` varchar
- `code_hash` varchar
- `purpose` enum: `verify_email`, `reset_password`
- `expires_at` timestamptz
- `used_at` timestamptz, nullable
- `attempts` integer, default 0
- `created_at` timestamptz

Talablar:

- Kod plain text holatda databasega yozilmasin.
- Kod muddati default 10 daqiqa.
- Maksimal urinishlar soni 5 ta.
- Yangi kod yuborilganda avvalgi aktiv kodlar bekor qilinadi.

### 5.3. refresh_tokens

Maydonlar:

- `id` UUID, primary key
- `user_id` UUID, foreign key users.id
- `token_hash` varchar, unique
- `jti` varchar, unique
- `expires_at` timestamptz
- `revoked_at` timestamptz, nullable
- `created_at` timestamptz
- `created_by_ip` inet yoki varchar, nullable
- `user_agent` text, nullable

Talablar:

- Refresh token databasega plain text yozilmasin.
- Logout qilinganda refresh token revoke qilinadi.
- Refresh qilinganda token rotation ishlatiladi: eski refresh token revoke
  qilinadi va yangi token beriladi.

## 6. JWT talablari

### 6.1. Access token

- Muddati: 15 daqiqa
- Algoritm: `RS256` yoki `HS256`
- Production uchun `RS256` tavsiya qilinadi.
- Claimlar:
  - `sub`: user id
  - `email`
  - `role`
  - `type`: `access`
  - `iat`
  - `exp`
  - `jti`

### 6.2. Refresh token

- Muddati: 7 kun
- Claimlar:
  - `sub`: user id
  - `type`: `refresh`
  - `iat`
  - `exp`
  - `jti`

### 6.3. Token xavfsizligi

- Access token client tomonidan `Authorization: Bearer <token>` headerida yuboriladi.
- Refresh token xavfsiz saqlanishi kerak.
- Backend refresh tokenni hash qilib databasega yozadi.
- Token secret/private key `.env` orqali beriladi.
- Expired, revoked yoki noto'g'ri tokenlar 401 qaytaradi.

## 7. API endpointlar

Base prefix: `/api/v1/auth`

### 7.1. Register

`POST /register`

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123!",
  "role": "candidate"
}
```

Response: `201 Created`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "candidate",
  "is_email_verified": false
}
```

Jarayon:

1. Email lowercase qilinadi.
2. Email unique ekanligi tekshiriladi.
3. Parol validatsiyadan o'tadi.
4. Parol hash qilinadi.
5. User yaratiladi.
6. Email verification code yaratiladi.
7. Kod emailga yuboriladi.

Xatolar:

- 400 - noto'g'ri parol yoki noto'g'ri role
- 409 - email allaqachon mavjud

### 7.2. Verify email

`POST /verify-email`

Request:

```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

Response: `200 OK`

```json
{
  "message": "Email verified successfully"
}
```

Talablar:

- Kod 6 xonali raqam bo'ladi.
- Kod muddati tugamagan bo'lishi kerak.
- Kod ishlatilmagan bo'lishi kerak.
- Muvaffaqiyatli tasdiqlanganda `users.is_email_verified = true`.

### 7.3. Resend verification code

`POST /resend-verification-code`

Request:

```json
{
  "email": "user@example.com"
}
```

Response: `200 OK`

```json
{
  "message": "Verification code sent"
}
```

Talablar:

- Rate limit: bitta email uchun 60 soniyada 1 marta.
- User mavjud bo'lmasa ham umumiy javob qaytishi mumkin, lekin ichki logda
  qayd qilinadi. Bu email enumeration xavfini kamaytiradi.

### 7.4. Login

`POST /login`

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

Response: `200 OK`

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "candidate",
    "is_email_verified": true
  }
}
```

Talablar:

- Email yoki parol xato bo'lsa umumiy xabar qaytariladi.
- `is_active = false` bo'lsa login qilinmaydi.
- Email tasdiqlanmagan foydalanuvchi uchun login siyosati aniq bo'lishi kerak.
  Tavsiya: login ruxsat etilmaydi va email tasdiqlash talab qilinadi.
- Muvaffaqiyatli loginda `last_login_at` yangilanadi.

### 7.5. Refresh token

`POST /refresh`

Request:

```json
{
  "refresh_token": "jwt"
}
```

Response: `200 OK`

```json
{
  "access_token": "new-jwt",
  "refresh_token": "new-refresh-jwt",
  "token_type": "bearer",
  "expires_in": 900
}
```

Talablar:

- Token type `refresh` bo'lishi kerak.
- Token database hash bilan tekshiriladi.
- Revoked yoki expired token qabul qilinmaydi.
- Rotation ishlaydi.

### 7.6. Logout

`POST /logout`

Request:

```json
{
  "refresh_token": "jwt"
}
```

Response: `204 No Content`

Talablar:

- Berilgan refresh token revoke qilinadi.
- Access token qisqa muddatli bo'lgani uchun blacklist talab qilinmaydi.

### 7.7. Forgot password

`POST /forgot-password`

Request:

```json
{
  "email": "user@example.com"
}
```

Response: `200 OK`

```json
{
  "message": "If the email exists, reset code has been sent"
}
```

Talablar:

- Email mavjud bo'lmasa ham bir xil javob qaytariladi.
- Reset code emailga yuboriladi.
- Rate limit: bitta email uchun 60 soniyada 1 marta.

### 7.8. Reset password

`POST /reset-password`

Request:

```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "NewStrongPass123!"
}
```

Response: `200 OK`

```json
{
  "message": "Password reset successfully"
}
```

Talablar:

- Kod `reset_password` purpose bilan tekshiriladi.
- Yangi parol eski paroldan farq qilishi kerak.
- Muvaffaqiyatli resetdan keyin foydalanuvchining barcha aktiv refresh
  tokenlari revoke qilinadi.

### 7.9. Current user

`GET /me`

Header:

```http
Authorization: Bearer <access_token>
```

Response: `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "candidate",
  "is_email_verified": true,
  "created_at": "2026-05-08T00:00:00Z"
}
```

### 7.10. Change password

`POST /change-password`

Header:

```http
Authorization: Bearer <access_token>
```

Request:

```json
{
  "old_password": "StrongPass123!",
  "new_password": "NewStrongPass123!"
}
```

Response: `200 OK`

```json
{
  "message": "Password changed successfully"
}
```

Talablar:

- Eski parol to'g'ri bo'lishi shart.
- Yangi parol validatsiyadan o'tadi.
- Muvaffaqiyatli o'zgargandan keyin barcha refresh tokenlar revoke qilinadi.

## 8. Parol siyosati

Minimal talablar:

- Kamida 8 belgi
- Kamida 1 katta harf
- Kamida 1 kichik harf
- Kamida 1 raqam
- Kamida 1 maxsus belgi
- Email bilan bir xil bo'lmasin

Parol hash:

- Argon2id yoki bcrypt ishlatiladi.
- Hash konfiguratsiyasi `.env` orqali emas, koddagi xavfsiz default orqali
  boshqariladi.

## 9. Email yuborish

Email provider abstraction bo'lishi kerak:

- Development: console yoki Mailhog
- Production: SMTP, SendGrid, Mailgun yoki boshqa provider

Email turlari:

- Email verification code
- Password reset code

Email shablonlari:

- Subject
- Plain text
- HTML

Talablar:

- Email yuborish asinxron bo'lishi kerak.
- Email yuborish xatosi log qilinadi.
- Register vaqtida user yaratilgan bo'lsa, email yuborish xatosi userni
  avtomatik o'chirmasligi kerak. Endpoint mos xato yoki qayta yuborish
  imkoniyatini qaytaradi.

## 10. Rate limiting va xavfsizlik

Majburiy talablar:

- Login endpoint uchun IP asosida rate limit.
- Email code yuborish endpointlari uchun email va IP asosida rate limit.
- Kod tekshirishda maksimal urinishlar.
- CORS sozlamalari `.env` orqali.
- Request body validatsiyasi Pydantic orqali.
- Xatolik xabarlari email enumerationga yo'l qo'ymasligi kerak.
- Secretlar repositoryga commit qilinmaydi.
- Productionda debug o'chiq bo'ladi.
- Database migrationlar Alembic orqali yuritiladi.
- Audit uchun muhim auth hodisalari log qilinadi:
  - register
  - verify email
  - login success/failure
  - refresh
  - logout
  - forgot password
  - reset password
  - change password

## 11. Project strukturasi

Tavsiya qilingan minimal tuzilma:

```text
app/
  main.py
  core/
    config.py
    security.py
    logging.py
  db/
    session.py
    base.py
  modules/
    auth/
      router.py
      schemas.py
      models.py
      service.py
      repository.py
      dependencies.py
      email.py
      exceptions.py
    users/
      models.py
      schemas.py
      repository.py
  migrations/
tests/
  auth/
    test_register.py
    test_verify_email.py
    test_login.py
    test_refresh.py
    test_password_reset.py
docker/
  entrypoint.sh
Dockerfile
docker-compose.yml
.env.example
pyproject.toml
alembic.ini
```

## 12. Konfiguratsiya

`.env.example` ichida quyidagilar bo'lishi kerak:

```env
APP_ENV=local
APP_DEBUG=true
APP_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/headhunter
REDIS_URL=redis://redis:6379/0

SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=no-reply@example.com

CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 13. Docker talablari

Dockerfile:

- Multi-stage build bo'lishi tavsiya qilinadi.
- Non-root user bilan ishga tushiriladi.
- Healthcheck qo'shiladi.

Docker Compose servislar:

- `api` - FastAPI app
- `db` - PostgreSQL
- `redis` - Redis
- `mailhog` yoki `mailpit` - local email test uchun

Buyruqlar:

```bash
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api pytest
```

## 14. Test talablari

Kamida quyidagi testlar yoziladi:

- Register muvaffaqiyatli o'tishi
- Duplicate email 409 qaytarishi
- Email verification code yuborilishi
- Noto'g'ri verification code rad qilinishi
- Muddati o'tgan code rad qilinishi
- Login muvaffaqiyatli o'tishi
- Noto'g'ri parol rad qilinishi
- Email tasdiqlanmagan user login qila olmasligi
- Refresh token rotation ishlashi
- Revoked refresh token rad qilinishi
- Logout refresh tokenni revoke qilishi
- Forgot password enumeration qilmasligi
- Reset password barcha refresh tokenlarni revoke qilishi
- Change password eski parolni talab qilishi
- `/me` faqat access token bilan ishlashi

## 15. Qabul mezonlari

Auth moduli tayyor hisoblanadi, agar:

- Barcha endpointlar ishlasa va OpenAPI hujjatlarida ko'rinsa.
- Database migrationlar toza ishga tushsa.
- Docker Compose orqali API, PostgreSQL, Redis va email test servisi ishlasa.
- JWT access/refresh token oqimi to'liq ishlasa.
- Email verification va password reset kodlari emailga yuborilsa.
- Kodlar databasega hash ko'rinishida yozilsa.
- Rate limiting asosiy auth endpointlarda ishlasa.
- Testlar muvaffaqiyatli o'tsa.
- `.env.example` bor bo'lsa va secretlar repositoryga tushmasa.
- Lint va type check xatolarsiz o'tsa.

## 16. Keyingi bosqichlarga tayyorgarlik

Auth moduli quyidagilarga tayyor bo'lishi kerak:

- Kandidat profilini `user_id` orqali bog'lash
- Employer kompaniya profilini `user_id` orqali bog'lash
- Role based access control dependencylari
- Admin endpointlarni himoyalash
- Social login yoki OAuth qo'shish imkoniyati
- 2FA qo'shish imkoniyati
