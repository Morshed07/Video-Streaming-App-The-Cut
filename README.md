# DramaSphere Backend 🎬

A scalable Django-powered backend for **DramaSphere**, a modern video streaming platform focused on drama content, featuring **parental controls**, **monthly voting systems**, subscription management, and cloud-native media delivery using **AWS S3 + CDN**.

---

## 🚀 Features

* 🔐 JWT Authentication & User Management
* 🎥 Video Streaming API
* 📂 Categories & Tags
* ❤️ Favorites & Watch History
* ⭐ Reviews & Helpful Votes
* 🏆 Monthly Award Voting System
* 👨‍👩‍👧 Parental Control / Kids Mode
* 🔔 Notification System
* 💳 Subscription Management with RevenueCat
* ☁️ AWS S3 Media Storage
* 🌍 CDN Optimized Streaming
* 🛡 Django Admin Dashboard
* ⚡ REST API using DRF
* 📈 Optimized PostgreSQL Architecture

---

# 🏗 Tech Stack

| Technology            | Usage                   |
| --------------------- | ----------------------- |
| Python                | Backend Language        |
| Django                | Web Framework           |
| Django REST Framework | API Development         |
| PostgreSQL            | Database                |
| Redis                 | Caching                 |
| Celery                | Background Jobs         |
| AWS S3                | File Storage            |
| CDN                   | Global Content Delivery |
| RevenueCat            | Subscription Management |
| JWT                   | Authentication          |
| Gunicorn              | Production Server       |
| Nginx                 | Reverse Proxy           |

---

# 📦 Core Modules

## 👤 Authentication & Users

* User Registration/Login
* OTP Verification
* JWT Authentication
* User Profiles
* Subscription Tracking
* Kids Mode PIN Protection

---

## 🎬 Video Management

* Video Upload & Streaming
* Featured Videos
* Trending Videos
* Categories & Tags
* Age Ratings
* Audience Filtering
* Publishing Workflow

---

## 👨‍👩‍👧 Parental Controls

DramaSphere includes advanced parental safety features:

* Kids Mode
* PIN Protected Access
* Kids-friendly content filtering
* Audience type restrictions
* Age-rated videos

---

## 🏆 Monthly Award Voting System

Users can:

* Vote for videos monthly
* Participate in award events
* Track rankings
* View winning videos

Database entities:

* `award_award`
* `award_awardvote`
* `award_videoaward`

---

## ⭐ Review System

Features:

* Video Reviews
* Helpful Votes
* Review Ranking
* Community Engagement

---

## ❤️ User Engagement

* Favorite Videos
* Watch History
* Continue Watching
* Notifications
* Likes & Views Tracking

---

# ☁️ AWS S3 + CDN Integration

DramaSphere uses:

* **AWS S3** for secure and scalable media storage
* **CDN** for high-speed global content delivery

Benefits:

* Faster streaming
* Lower server load
* Better scalability
* Improved user experience

---

# 💳 RevenueCat Integration

Subscription management is powered by **RevenueCat**.

Supported Features:

* Monthly subscriptions
* Premium access control
* Subscription validation
* Expiration tracking
* Cross-platform sync

---

# 🗄 Database Architecture

The backend architecture includes:

* Users
* Videos
* Categories
* Tags
* Favorites
* Reviews
* Notifications
* Awards
* Watch History
* Permissions & Groups

---

# 📊 ER Diagram

The following ER diagram represents the complete backend database architecture:

![DramaSphere Database ERD](./Dramasphere.png)

---

# ⚙️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/dramasphere-backend.git

cd dramasphere-backend
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

#### Linux / macOS

```bash
source venv/bin/activate
```

#### Windows

```bash
venv\Scripts\activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Environment Variables

Create `.env`

```env
DEBUG=True

SECRET_KEY=your_secret_key

ALLOWED_HOSTS=*

DATABASE_URL=postgresql://postgres:password@localhost:5432/dramasphere

REDIS_URL=redis://127.0.0.1:6379

AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket
AWS_S3_REGION_NAME=your_region
AWS_S3_CUSTOM_DOMAIN=cdn.example.com

REVENUECAT_API_KEY=your_revenuecat_key

JWT_SECRET_KEY=your_jwt_secret
```

---

# 🛠 Run Migrations

```bash
python manage.py migrate
```

---

# 👤 Create Superuser

```bash
python manage.py createsuperuser
```

---

# ▶️ Run Development Server

```bash
python manage.py runserver
```

---

# ⚡ Run Celery Worker

```bash
celery -A config worker -l info
```

---

# 🔥 Start Redis

```bash
redis-server
```

---

# 📡 Example API Routes

```http
/api/auth/
/api/videos/
/api/categories/
/api/reviews/
/api/favorites/
/api/awards/
/api/notifications/
```

---

# 🔐 Authentication

DramaSphere uses JWT Authentication.

Example:

```http
Authorization: Bearer <token>
```

---

# 📁 Media Handling

Uploaded media is stored in:

* AWS S3
* Delivered through CDN

Supported files:

* Video files
* Thumbnails
* Profile images

---

# 🚀 Recommended Production Stack

* Ubuntu VPS
* Nginx
* Gunicorn
* PostgreSQL
* Redis
* Celery
* Supervisor
* Cloudflare CDN

---

# 🧪 Future Improvements

* AI Recommendations
* Live Streaming
* Smart Content Moderation
* Multi-language Subtitles
* Offline Downloads
* Social Features

---

# 🤝 Contributing

Pull requests are welcome.

Steps:

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push branch
5. Open Pull Request

---

# 📄 License

MIT License

---

# 👨‍💻 Developed By

**DramaSphere Backend Team**

Built with ❤️ using Django, DRF, PostgreSQL, AWS S3, and RevenueCat.
