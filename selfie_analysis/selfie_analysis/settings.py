import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["*"]),
    SKIN_ANALYSIS_PROVIDER=(str, "perfectcorp"),
    # 공개 문서 발췌본에 S2S 호출의 base host가 명시돼 있지 않아 기본값을 두지 않는다.
    # API 콘솔(https://yce.makeupar.com/api-console/en/api-keys/)에서 확인해 .env에 채울 것.
    PERFECTCORP_BASE_URL=(str, ""),
    PERFECTCORP_API_KEY=(str, ""),
    PERFECTCORP_FILE_UPLOAD_PATH=(str, ""),
    PERFECTCORP_DST_ACTIONS=(
        list,
        ["moisture", "firmness", "redness", "pore", "wrinkle", "age_spot"],
    ),
    PERFECTCORP_WEBHOOK_SECRET=(str, ""),
    PERFECTCORP_POLL_INTERVAL_SECONDS=(float, 3.0),
    SKIN_ANALYSIS_POLL_TIMEOUT_SECONDS=(float, 120.0),
    SELFIE_UPLOAD_RSA_PRIVATE_KEY=(str, ""),
    INTERNAL_SERVICE_TOKEN=(str, ""),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-selfie-analysis")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "analysis",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "selfie_analysis.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "selfie_analysis.wsgi.application"


# Database
# 프로덕션에서는 메인 서버와 동일한 MySQL(DATABASE_URL)을 가리켜 selfie_analysis /
# selfie_analysis_detail 테이블을 공유하는 것이 기본 전제. 로컬 개발 시엔 sqlite로 폴백.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}


# --- 셀카 업로드 하이브리드 암호화 (analysis/crypto.py) ---
SELFIE_UPLOAD_RSA_PRIVATE_KEY = env("SELFIE_UPLOAD_RSA_PRIVATE_KEY").replace("\\n", "\n")

# --- 메인 서버 ↔ 이 마이크로서비스 간 임시 인증 (analysis/permissions.py, 설계 미확정) ---
INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN")

# --- 피부 분석 벤더 (analysis/providers) ---
SKIN_ANALYSIS_PROVIDER = env("SKIN_ANALYSIS_PROVIDER")
SKIN_ANALYSIS_POLL_TIMEOUT_SECONDS = env.float("SKIN_ANALYSIS_POLL_TIMEOUT_SECONDS")

PERFECTCORP_BASE_URL = env("PERFECTCORP_BASE_URL")
PERFECTCORP_API_KEY = env("PERFECTCORP_API_KEY")

PERFECTCORP_FILE_UPLOAD_PATH = env("PERFECTCORP_FILE_UPLOAD_PATH")
PERFECTCORP_DST_ACTIONS = env.list("PERFECTCORP_DST_ACTIONS")
PERFECTCORP_POLL_INTERVAL_SECONDS = env.float("PERFECTCORP_POLL_INTERVAL_SECONDS")
PERFECTCORP_WEBHOOK_SECRET = env("PERFECTCORP_WEBHOOK_SECRET")

CHRONO_WEBHOOK_URL = env('CHRONO_WEBHOOK_URL', default='http://127.0.0.1:8000/selfie/selfie-analyses/webhook/')
