"""
Django + DRF code generator for InfraNest.

Renders the Jinja2 templates under ``templates/django`` and adds the
supporting project scaffolding (settings, manage.py, admin, env template,
README) needed to make the generated project actually runnable.
"""

import json
import os
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .base_generator import BaseGenerator

# templates/django lives two levels above this file: core/generators/.. -> core/.. -> repo root
_TEMPLATES_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "templates", "django")
)


class DjangoGenerator(BaseGenerator):
    """Generates a Django + Django REST Framework project from a DSL spec."""

    def __init__(self, templates_dir: str = _TEMPLATES_ROOT):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        # Vanilla Jinja2 environments (unlike Flask's) do not ship a `tojson`
        # filter out of the box, but the templates rely on it.
        self.env.filters["tojson"] = lambda value: json.dumps(value)

    def generate(self, spec: Dict[str, Any]) -> Dict[str, str]:
        context = self.build_context(spec)
        app_name = self._app_name(context)
        project_name = context["meta"]["name"].replace("-", "_")

        files: Dict[str, str] = {}

        files[f"{app_name}/models.py"] = self._render("models.py.j2", context)
        files[f"{app_name}/serializers.py"] = self._render("serializers.py.j2", context)
        files[f"{app_name}/views.py"] = self._render("views.py.j2", context)
        files[f"{app_name}/urls.py"] = self._render("urls.py.j2", context)
        files["requirements.txt"] = self._render("requirements.txt.j2", context)
        files["Dockerfile"] = self._render("Dockerfile.j2", context)

        files[f"{app_name}/__init__.py"] = ""
        files[f"{app_name}/apps.py"] = self._apps_py(app_name)
        files[f"{app_name}/admin.py"] = self._admin_py(context, app_name)
        files[f"{project_name}/__init__.py"] = ""
        files[f"{project_name}/settings.py"] = self._settings_py(context, app_name, project_name)
        files[f"{project_name}/urls.py"] = self._project_urls_py(context, app_name)
        files[f"{project_name}/wsgi.py"] = self._wsgi_py(project_name)
        files[f"{project_name}/asgi.py"] = self._asgi_py(project_name)
        files["manage.py"] = self._manage_py(project_name)
        files[".env.example"] = self._env_example(context)
        files["README.md"] = self._readme(context, app_name)
        files[".dockerignore"] = "*.pyc\n__pycache__/\n.env\nvenv/\ndb.sqlite3\n"

        return files

    # -- template rendering -------------------------------------------------

    def _render(self, template_name: str, context: Dict[str, Any]) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)

    # -- helpers for files that don't need Jinja2 ---------------------------

    def _app_name(self, context: Dict[str, Any]) -> str:
        name = context["meta"]["name"].replace("-", "_")
        return f"{name}_app"

    def _apps_py(self, app_name: str) -> str:
        class_name = "".join(part.capitalize() for part in app_name.split("_"))
        return (
            "from django.apps import AppConfig\n\n\n"
            f"class {class_name}Config(AppConfig):\n"
            "    default_auto_field = 'django.db.models.BigAutoField'\n"
            f"    name = '{app_name}'\n"
        )

    def _admin_py(self, context: Dict[str, Any], app_name: str) -> str:
        models = list(context.get("models", {}).keys())
        lines = ["from django.contrib import admin", f"from .models import {', '.join(models)}" if models else "", ""]
        for model_name in models:
            lines.append(f"admin.site.register({model_name})")
        return "\n".join(line for line in lines if line is not None) + "\n"

    def _settings_py(self, context: Dict[str, Any], app_name: str, project_name: str) -> str:
        database = context["meta"].get("database", "postgresql")
        auth = context["auth"]
        jwt_enabled = auth.get("provider") == "jwt"

        if database == "postgresql":
            db_config = (
                "DATABASES = {\n"
                "    'default': {\n"
                "        'ENGINE': 'django.db.backends.postgresql',\n"
                "        'NAME': config('DB_NAME', default='" + project_name + "'),\n"
                "        'USER': config('DB_USER', default='postgres'),\n"
                "        'PASSWORD': config('DB_PASSWORD', default=''),\n"
                "        'HOST': config('DB_HOST', default='localhost'),\n"
                "        'PORT': config('DB_PORT', default='5432'),\n"
                "    }\n"
                "}\n"
            )
        elif database == "mysql":
            db_config = (
                "DATABASES = {\n"
                "    'default': {\n"
                "        'ENGINE': 'django.db.backends.mysql',\n"
                "        'NAME': config('DB_NAME', default='" + project_name + "'),\n"
                "        'USER': config('DB_USER', default='root'),\n"
                "        'PASSWORD': config('DB_PASSWORD', default=''),\n"
                "        'HOST': config('DB_HOST', default='localhost'),\n"
                "        'PORT': config('DB_PORT', default='3306'),\n"
                "    }\n"
                "}\n"
            )
        else:
            db_config = (
                "DATABASES = {\n"
                "    'default': {\n"
                "        'ENGINE': 'django.db.backends.sqlite3',\n"
                "        'NAME': BASE_DIR / 'db.sqlite3',\n"
                "    }\n"
                "}\n"
            )

        rest_auth = ""
        jwt_apps = ""
        jwt_settings = ""
        if jwt_enabled:
            jwt_apps = "    'rest_framework_simplejwt',\n"
            rest_auth = (
                "REST_FRAMEWORK = {\n"
                "    'DEFAULT_AUTHENTICATION_CLASSES': (\n"
                "        'rest_framework_simplejwt.authentication.JWTAuthentication',\n"
                "    ),\n"
                "    'DEFAULT_PERMISSION_CLASSES': (\n"
                "        'rest_framework.permissions.IsAuthenticatedOrReadOnly',\n"
                "    ),\n"
                "}\n"
            )
            jwt_settings = (
                "from datetime import timedelta\n\n"
                "SIMPLE_JWT = {\n"
                "    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),\n"
                "    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),\n"
                "}\n"
            )
        else:
            rest_auth = (
                "REST_FRAMEWORK = {\n"
                "    'DEFAULT_PERMISSION_CLASSES': (\n"
                "        'rest_framework.permissions.IsAuthenticatedOrReadOnly',\n"
                "    ),\n"
                "}\n"
            )

        auth_user_model_setting = ""
        if auth.get("user_model") in context.get("models", {}):
            auth_user_model_setting = f"AUTH_USER_MODEL = '{app_name}.{auth['user_model']}'\n"

        return (
            "\"\"\"\n"
            f"Django settings for {project_name}, generated by InfraNest.\n"
            "\"\"\"\n\n"
            "from pathlib import Path\n"
            "from decouple import config\n\n"
            "BASE_DIR = Path(__file__).resolve().parent.parent\n\n"
            "SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')\n"
            "DEBUG = config('DEBUG', default=False, cast=bool)\n"
            "ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])\n\n"
            "INSTALLED_APPS = [\n"
            "    'django.contrib.admin',\n"
            "    'django.contrib.auth',\n"
            "    'django.contrib.contenttypes',\n"
            "    'django.contrib.sessions',\n"
            "    'django.contrib.messages',\n"
            "    'django.contrib.staticfiles',\n"
            "    'rest_framework',\n"
            "    'django_filters',\n"
            "    'corsheaders',\n"
            f"{jwt_apps}"
            f"    '{app_name}',\n"
            "]\n\n"
            "MIDDLEWARE = [\n"
            "    'corsheaders.middleware.CorsMiddleware',\n"
            "    'django.middleware.security.SecurityMiddleware',\n"
            "    'django.contrib.sessions.middleware.SessionMiddleware',\n"
            "    'django.middleware.common.CommonMiddleware',\n"
            "    'django.middleware.csrf.CsrfViewMiddleware',\n"
            "    'django.contrib.auth.middleware.AuthenticationMiddleware',\n"
            "    'django.contrib.messages.middleware.MessageMiddleware',\n"
            "    'django.middleware.clickjacking.XFrameOptionsMiddleware',\n"
            "]\n\n"
            f"ROOT_URLCONF = '{project_name}.urls'\n\n"
            "TEMPLATES = [\n"
            "    {\n"
            "        'BACKEND': 'django.template.backends.django.DjangoTemplates',\n"
            "        'DIRS': [],\n"
            "        'APP_DIRS': True,\n"
            "        'OPTIONS': {\n"
            "            'context_processors': [\n"
            "                'django.template.context_processors.debug',\n"
            "                'django.template.context_processors.request',\n"
            "                'django.contrib.auth.context_processors.auth',\n"
            "                'django.contrib.messages.context_processors.messages',\n"
            "            ],\n"
            "        },\n"
            "    },\n"
            "]\n\n"
            f"WSGI_APPLICATION = '{project_name}.wsgi.application'\n\n"
            f"{db_config}\n"
            f"{auth_user_model_setting}"
            "AUTH_PASSWORD_VALIDATORS = [\n"
            "    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},\n"
            "    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},\n"
            "    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},\n"
            "    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},\n"
            "]\n\n"
            f"{rest_auth}\n"
            f"{jwt_settings}\n"
            "CORS_ALLOWED_ORIGINS = config(\n"
            "    'CORS_ALLOWED_ORIGINS',\n"
            "    default='http://localhost:3000,http://localhost:5173',\n"
            "    cast=lambda v: [s.strip() for s in v.split(',')],\n"
            ")\n\n"
            "LANGUAGE_CODE = 'en-us'\n"
            "TIME_ZONE = 'UTC'\n"
            "USE_I18N = True\n"
            "USE_TZ = True\n\n"
            "STATIC_URL = 'static/'\n"
            "STATIC_ROOT = BASE_DIR / 'staticfiles'\n\n"
            "DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'\n"
        )

    def _project_urls_py(self, context: Dict[str, Any], app_name: str) -> str:
        return (
            "from django.contrib import admin\n"
            "from django.urls import path, include\n"
            "from django.http import JsonResponse\n\n\n"
            "def health_check(request):\n"
            "    return JsonResponse({'status': 'healthy'})\n\n\n"
            "urlpatterns = [\n"
            "    path('admin/', admin.site.urls),\n"
            "    path('health/', health_check, name='health-check'),\n"
            f"    path('', include('{app_name}.urls')),\n"
            "]\n"
        )

    def _wsgi_py(self, project_name: str) -> str:
        return (
            "import os\n\n"
            "from django.core.wsgi import get_wsgi_application\n\n"
            f"os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')\n\n"
            "application = get_wsgi_application()\n"
        )

    def _asgi_py(self, project_name: str) -> str:
        return (
            "import os\n\n"
            "from django.core.asgi import get_asgi_application\n\n"
            f"os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')\n\n"
            "application = get_asgi_application()\n"
        )

    def _manage_py(self, project_name: str) -> str:
        return (
            "#!/usr/bin/env python\n"
            "\"\"\"Django's command-line utility for administrative tasks.\"\"\"\n"
            "import os\n"
            "import sys\n\n\n"
            "def main():\n"
            f"    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')\n"
            "    try:\n"
            "        from django.core.management import execute_from_command_line\n"
            "    except ImportError as exc:\n"
            "        raise ImportError(\n"
            "            'Could not import Django. Are you sure it is installed and '\n"
            "            'available on your PYTHONPATH environment variable? Did you '\n"
            "            'forget to activate a virtual environment?'\n"
            "        ) from exc\n"
            "    execute_from_command_line(sys.argv)\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )

    def _env_example(self, context: Dict[str, Any]) -> str:
        return (
            "SECRET_KEY=change-me-in-production\n"
            "DEBUG=True\n"
            "ALLOWED_HOSTS=localhost,127.0.0.1\n"
            f"DB_NAME={context['meta']['name'].replace('-', '_')}\n"
            "DB_USER=postgres\n"
            "DB_PASSWORD=\n"
            "DB_HOST=localhost\n"
            "DB_PORT=5432\n"
            "CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173\n"
        )

    def _readme(self, context: Dict[str, Any], app_name: str) -> str:
        meta = context["meta"]
        return (
            f"# {meta['name']}\n\n"
            f"{meta.get('description', '')}\n\n"
            "Generated by [InfraNest](https://github.com) from a DSL specification.\n\n"
            "## Setup\n\n"
            "```bash\n"
            "cp .env.example .env\n"
            "python -m venv venv && source venv/bin/activate\n"
            "pip install -r requirements.txt\n"
            "python manage.py migrate\n"
            "python manage.py createsuperuser\n"
            "python manage.py runserver\n"
            "```\n\n"
            "## Docker\n\n"
            "```bash\n"
            "docker build -t "
            f"{meta['name']} .\n"
            f"docker run -p 8000:8000 --env-file .env {meta['name']}\n"
            "```\n\n"
            f"## App\n\nGenerated Django app: `{app_name}`\n"
        )
