# EduTest Platform — Django REST API

Ta'lim markazlari uchun onlayn test platformasi.
Mualllimlar darslarni yaratadi, o'quvchilar test topshiradi.

## Texnologiyalar

- **Django 4.2** — asosiy web framework
- **Django REST Framework** — REST API
- **JWT (SimpleJWT)** — autentifikatsiya (mobil ilovalar uchun tayyor)
- **PostgreSQL** — ma'lumotlar bazasi
- **drf-yasg** — Swagger API dokumentatsiyasi

---

## Loyiha tuzilmasi

```
django-edu-platform/
├── eduplatform/          # Asosiy sozlamalar (settings, urls)
├── users/                # Foydalanuvchilar (teacher/student)
├── courses/              # Kurslar va guruhlar
├── tests_app/            # Mavzular, savollar, test topshirish
├── results/              # Natijalar va analitika
├── ai_generator/         # AI yordamida savol generatsiya
├── manage.py
├── requirements.txt
└── .env.example
```

---

## O'rnatish va ishga tushirish

### 1. Virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 3. .env fayl yaratish

```bash
cp .env.example .env
# .env faylni tahrirlang va kerakli qiymatlarni kiriting
```

### 4. Ma'lumotlar bazasini tayyorlash

**SQLite (tezkor sinash uchun):**
```bash
python manage.py migrate
python manage.py seed_data          # Demo ma'lumotlar qo'shish
```

**PostgreSQL:**
```bash
# .env ga DATABASE_URL ni o'rnating:
# DATABASE_URL=postgres://user:password@localhost:5432/edu_platform

# Postgres bazasini yarating:
createdb edu_platform

python manage.py migrate
python manage.py seed_data
```

### 5. Serverni ishga tushirish

```bash
python manage.py runserver
```

Server manzili: http://localhost:8000

---

## API Dokumentatsiya

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

---

## Login Credentials (seed_data dan keyin)

| Rol     | Username | Password    |
|---------|----------|-------------|
| Teacher | teacher  | teacher123  |
| Student | ali      | student123  |
| Student | fatima   | student123  |
| Student | sardor   | student123  |

---

## Asosiy API Endpointlari

### Autentifikatsiya

```http
POST /api/v1/auth/login/
{"username": "teacher", "password": "teacher123"}
→ {"access": "...", "refresh": "...", "user": {...}}

POST /api/v1/auth/refresh/
{"refresh": "..."}
→ {"access": "..."}

GET  /api/v1/auth/me/
→ {"id": 1, "username": "teacher", "role": "teacher", ...}
```

### Kurslar

```http
GET    /api/v1/courses/          # Barcha kurslar
POST   /api/v1/courses/          # Yangi kurs (teacher)
GET    /api/v1/courses/{id}/
PATCH  /api/v1/courses/{id}/     # Yangilash (teacher)
DELETE /api/v1/courses/{id}/     # O'chirish (teacher)
```

### Guruhlar

```http
GET    /api/v1/groups/
POST   /api/v1/groups/           # (teacher)
GET    /api/v1/groups/{id}/students/
POST   /api/v1/groups/{id}/add-student/
```

### Mavzular va savollar

```http
GET    /api/v1/topics/           # ?group_id=1&date=2024-01-15
POST   /api/v1/topics/           # (teacher)
GET    /api/v1/questions/topic/{topic_id}/   # (teacher)
POST   /api/v1/questions/topic/{topic_id}/   # Savol qo'shish (teacher)
```

### Test topshirish (student)

```http
GET  /api/v1/tests/{topic_id}/start/
# → Tasodifiy tartibda savollar (to'g'ri javob ko'rsatilmaydi)

POST /api/v1/tests/{topic_id}/submit/
{"answers": [{"question_id": 1, "selected_option": "A"}, ...]}
# → Ball, natija, to'g'ri/noto'g'ri javoblar
```

### Natijalar

```http
GET /api/v1/results/                    # O'z natijalari (student) / barchasi (teacher)
GET /api/v1/results/{id}/               # Batafsil natija

GET /api/v1/analytics/dashboard/        # Umumiy statistika (teacher)
GET /api/v1/analytics/student/{id}/     # O'quvchi progressi
GET /api/v1/analytics/group/{id}/       # Guruh analitikasi
GET /api/v1/analytics/recent-activity/  # So'nggi testlar
```

### AI Savol Generatsiya

```http
POST /api/v1/ai/generate-questions/
{"topic_id": 5, "count": 5}
# → GPT yordamida 5 ta savol yaratiladi va bazaga qo'shiladi
```

---

## JWT Autentifikatsiya

Barcha so'rovlarda token yuborish:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

**JavaScript/React:**
```javascript
const response = await fetch('/api/v1/topics/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  }
});
```

**Android (Retrofit):**
```kotlin
@GET("api/v1/topics/")
suspend fun getTopics(
    @Header("Authorization") token: String
): List<Topic>
```

---

## Kelajakda mobil ilovaga o'tkazish

Bu API allaqachon mobil ilovalar uchun tayyor!

1. **Android**: Retrofit + OkHttp → JWT tokenlarni SharedPreferences ga saqlang
2. **iOS**: URLSession yoki Alamofire → Keychain ga JWT saqlang
3. **Flutter**: http yoki dio kutubxonasi
4. Barcha endpoint'lar bir xil ishlaydi — faqat frontend o'zgaradi

---

## Xavfsizlik (Anti-Cheat)

- ✅ Server-side grading (javoblar client'da saqlanmaydi)
- ✅ Correct answers hech qachon student'ga ko'rsatilmaydi
- ✅ Savollar va variantlar tasodifiy tartibda beriladi
- ✅ `is_submitted=True` bo'lgach, javoblar o'zgartirilmaydi
- ✅ Har bir urinish bazaga saqlanadi
- ✅ Maksimal urinish soni tekshiriladi
- ✅ Sana bo'yicha kirish cheklovi
