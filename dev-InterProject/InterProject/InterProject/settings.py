"""
Django settings for apps project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-!@5lu_jeycu=3u+hw(c@*$csdcs9r9i$^df4n(#pgrpk+_5cxj"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# 允许访问的ip
ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",  # 启用后台管理
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    'django_apscheduler',
    "django.contrib.staticfiles",
    'django_cas_ng',
    # 就业推荐相关
    'jobapps.job.apps.JobConfig',
    'jobapps.work.apps.WorkConfig',
    'jobapps.user.apps.UserConfig',
    'jobapps.company.apps.CompanyConfig',
    'jobapps.student.apps.StudentConfig',
    'jobapps.resume.apps.ResumeConfig',
    'jobapps.recruit.apps.RecruitConfig',
    'jobapps.middle.apps.MiddleConfig',
    # 语音克隆相关
    # 知识图谱相关
    'Graphapps.apps.GraphappsConfig',
    "rest_framework",  # 用于开发RESTful API
    'rest_framework.authtoken',  # DRF自带的Token认证
    'drf_yasg',
    'corsheaders',
    # 'django_apscheduler',  # 定时器 - 暂时禁用
    # 'django_cas_ng'  # cas客户端 - 暂时禁用
]
# cas服务端配置
MAMA_CAS_SERVICES = [
    {
        'SERVICE': 'jyxxw.xidian.edu.cn/examIDS',
        'CALLBACKS': [
            'mama_cas.callbacks.user_model_attributes',  # 返回除了password的所有Field
            # 'mama_cas.callbacks.user_name_attributes', # 只返回 username
        ],
        'LOGOUT_ALLOW': True,
        'LOGOUT_URL': 'http://127.0.1.1:8000/accounts/callback',
    },
]
# cache缓存配置
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cache1",  # 缓存实例的名称，可以自定义
    }
}
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 'django_cas_ng.middleware.CASMiddleware',  # 添加cas客户端的中间件类 - 暂时禁用
]
# 指定授权认证的后端
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # 'django_cas_ng.backends.CASBackend',  # 暂时禁用
)
# CAS服务器URL和版本
CAS_SERVER_URL = 'https://ids.xidian.edu.cn/authserver/'
CAS_VERSION = '3'
# 存入所有 CAS 服务端返回的 User 数据。
CAS_APPLY_ATTRIBUTES_TO_USER = True

# 允许所有来源访问
# CORS_ALLOW_CREDENTIALS = True  # 允许携带Cookie
CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = "InterProject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "InterProject.wsgi.application"

CORS_ALLOW_ALL_ORIGINS = True

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     },
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jobrec',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': 3306,
        'OPTIONS': {'charset': 'utf8mb4'},
    },
}
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)


# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "static/"

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, "static")
# )

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',  # 默认分页类
    'PAGE_SIZE': 5,  # 每页数据量
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',  # 时间显示格式
    'DEFAULT_RENDER_CLASSES': [
        'rest_framework.renders.JSONRenderer',
        'rest_framework.renders.BrowsableAPIRenderer',
    ],  # 返回response对象所用的类
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],  # 解析器，如何解析request请求中的request.data
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        'rest_framework.permissions.AllowAny'
    ],  # 权限相关配置
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],  # 认证相关配置
    "URL_FIELD_NAME": 'link',
    # 接口文档
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

AUTH_USER_MODEL = 'user.User'
# FORCE_SCRIPT_NAME = '/jobrec'
CSRF_COOKIE_DOMAIN = "jyxxw.xidian.edu.cn"
