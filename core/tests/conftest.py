"""
Shared pytest fixtures for the InfraNest core engine test suite.
"""

import copy
import sys
from pathlib import Path

import pytest

# Belt-and-suspenders alongside pytest.ini's `pythonpath = .`: make sure
# `core/` is importable as the package root (matches how app.py resolves
# `from generators...` / `from parsers...` in production) even if these
# tests are collected from a different working directory or pytest.ini's
# rootdir-relative pythonpath doesn't get picked up by a given runner.
CORE_DIR = Path(__file__).resolve().parent.parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


@pytest.fixture
def minimal_dsl():
    """The smallest DSL spec that should pass validation."""
    return {
        "meta": {
            "name": "minimal-api",
            "version": "1.0.0",
            "framework": "django",
        },
        "models": {
            "Widget": {
                "fields": {
                    "id": {"type": "uuid", "primary_key": True, "auto_generated": True},
                    "name": {"type": "string", "required": True, "max_length": 100},
                }
            }
        },
    }


@pytest.fixture
def blog_dsl():
    """A realistic multi-model spec: FKs (including a self-referential FK),
    many_to_many, choice fields, and a hashed password - exercises the parts
    of each generator that plain CRUD scaffolding doesn't reach."""
    return {
        "meta": {
            "name": "blog-api",
            "description": "A blog API",
            "version": "1.0.0",
            "framework": "django",
            "database": "postgresql",
        },
        "auth": {
            "provider": "jwt",
            "user_model": "User",
            "required_fields": ["email", "password"],
        },
        "models": {
            "User": {
                "fields": {
                    "id": {"type": "uuid", "primary_key": True, "auto_generated": True},
                    "email": {"type": "string", "unique": True, "required": True, "max_length": 255},
                    "password": {"type": "string", "required": True, "hashed": True},
                    "is_active": {"type": "boolean", "default": True},
                    "created_at": {"type": "datetime", "auto_now_add": True},
                },
            },
            "Post": {
                "fields": {
                    "id": {"type": "uuid", "primary_key": True, "auto_generated": True},
                    "title": {"type": "string", "required": True, "max_length": 200},
                    "content": {"type": "text", "required": True},
                    "status": {
                        "type": "choice",
                        "choices": ["draft", "published", "archived"],
                        "default": "draft",
                    },
                    "author": {"type": "foreign_key", "model": "User", "on_delete": "cascade"},
                    "tags": {"type": "many_to_many", "model": "Tag"},
                    "created_at": {"type": "datetime", "auto_now_add": True},
                },
            },
            "Comment": {
                "fields": {
                    "id": {"type": "uuid", "primary_key": True, "auto_generated": True},
                    "content": {"type": "text", "required": True},
                    "author": {"type": "foreign_key", "model": "User", "on_delete": "cascade"},
                    "post": {"type": "foreign_key", "model": "Post", "on_delete": "cascade"},
                    # self-referential FK (threaded replies) - stresses
                    # dependency ordering / reverse-accessor collisions
                    "parent": {"type": "foreign_key", "model": "Comment", "on_delete": "cascade"},
                    "created_at": {"type": "datetime", "auto_now_add": True},
                },
            },
            "Tag": {
                "fields": {
                    "id": {"type": "uuid", "primary_key": True, "auto_generated": True},
                    "name": {"type": "string", "required": True, "unique": True, "max_length": 50},
                },
            },
        },
        "api": {"base_path": "/api/v1", "endpoints": []},
        "deployment": {"docker": {"port": 8000, "health_check": "/health"}},
    }


@pytest.fixture
def blog_dsl_for(blog_dsl):
    """Factory returning a copy of blog_dsl targeting a given framework."""

    def _make(framework: str):
        spec = copy.deepcopy(blog_dsl)
        spec["meta"]["framework"] = framework
        return spec

    return _make


@pytest.fixture
def app():
    """The real Flask app object (core/app.py), imported with `core/` as the
    package root so its internal `from generators...` imports resolve."""
    import app as core_app_module

    core_app_module.app.config.update(TESTING=True)
    return core_app_module.app


@pytest.fixture
def client(app):
    return app.test_client()
