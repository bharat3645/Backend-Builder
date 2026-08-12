"""
Tests for core/generators/*.py.

These go beyond "does it return a dict of strings" - they verify the
generated *content* is actually well-formed:
  - Django output must be syntactically valid Python (ast.parse).
  - Go output must have balanced braces/parens per file (a cheap proxy for
    "didn't truncate mid-statement" that doesn't require a Go toolchain).
  - Rails output's migration timestamps must respect FK dependency order,
    and strong-params must list scalar args before hash args (otherwise
    it's a Ruby SyntaxError).
"""

import ast
import copy
import re

import pytest

from generators.django_generator import DjangoGenerator
from generators.go_generator import GoGenerator
from generators.rails_generator import RailsGenerator
from parsers.dsl_parser import DSLParser


def _parsed(spec):
    return DSLParser().parse(spec)


# -- Django -------------------------------------------------------------


class TestDjangoGenerator:
    def test_generates_expected_files(self, blog_dsl_for):
        files = DjangoGenerator().generate(_parsed(blog_dsl_for("django")))
        assert "manage.py" in files
        assert ".env.example" in files
        assert "requirements.txt" in files
        assert any(f.endswith("models.py") for f in files)
        assert any(f.endswith("serializers.py") for f in files)
        assert any(f.endswith("views.py") for f in files)
        assert any(f.endswith("settings.py") for f in files)

    def test_all_python_files_are_syntactically_valid(self, blog_dsl_for):
        files = DjangoGenerator().generate(_parsed(blog_dsl_for("django")))
        for path, content in files.items():
            if path.endswith(".py"):
                try:
                    ast.parse(content, filename=path)
                except SyntaxError as exc:  # pragma: no cover - failure path
                    pytest.fail(f"{path} is not valid Python: {exc}\n---\n{content}")

    def test_minimal_model_still_produces_valid_meta_class(self, minimal_dsl):
        """A model with no `permissions`/ordering config used to render an
        empty `class Meta:` body -> IndentationError."""
        files = DjangoGenerator().generate(_parsed(minimal_dsl))
        models_py = next(v for k, v in files.items() if k.endswith("models.py"))
        ast.parse(models_py)  # would raise IndentationError on the old template
        assert "class Meta:" in models_py

    def test_self_referential_and_shared_target_fks_get_distinct_related_names(self, blog_dsl_for):
        files = DjangoGenerator().generate(_parsed(blog_dsl_for("django")))
        models_py = next(v for k, v in files.items() if k.endswith("models.py"))
        related_names = re.findall(r"related_name=['\"]([^'\"]+)['\"]", models_py)
        assert len(related_names) == len(set(related_names)), (
            f"duplicate related_name would raise Django's E304: {related_names}"
        )

    def test_requirements_txt_nonempty(self, minimal_dsl):
        files = DjangoGenerator().generate(_parsed(minimal_dsl))
        assert "djangorestframework" in files["requirements.txt"].lower()

    def test_simplejwt_pin_avoids_pkg_resources_importerror(self, minimal_dsl):
        """djangorestframework-simplejwt==5.3.0 imports `pkg_resources` at
        module load time and raises `ModuleNotFoundError: No module named
        'pkg_resources'` wherever setuptools isn't already present (which
        current Python/setuptools releases no longer guarantee) - verified
        by actually running `manage.py check` in a clean venv. Pin >=5.3.1,
        which uses importlib.metadata instead."""
        spec = copy.deepcopy(minimal_dsl)
        spec["auth"] = {"provider": "jwt", "user_model": "User", "required_fields": ["email", "password"]}
        files = DjangoGenerator().generate(_parsed(spec))
        match = re.search(r"djangorestframework-simplejwt==(\d+)\.(\d+)\.(\d+)", files["requirements.txt"])
        assert match, "expected a pinned djangorestframework-simplejwt version"
        major, minor, patch = (int(part) for part in match.groups())
        assert (major, minor, patch) >= (5, 3, 1)

    def test_preview_matches_generate_file_count(self, blog_dsl_for):
        spec = _parsed(blog_dsl_for("django"))
        gen = DjangoGenerator()
        preview = gen.preview(spec)
        files = gen.generate(spec)
        assert preview["file_count"] == len(files)


# -- Go Fiber -------------------------------------------------------------


def _assert_balanced(content: str, path: str):
    pairs = {"{": "}", "(": ")", "[": "]"}
    closers = set(pairs.values())
    stack = []
    for ch in content:
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in closers:
            assert stack and stack[-1] == ch, f"{path}: unbalanced '{ch}'"
            stack.pop()
    assert not stack, f"{path}: unclosed {stack}"


class TestGoGenerator:
    def test_generates_expected_files(self, blog_dsl_for):
        files = GoGenerator().generate(_parsed(blog_dsl_for("go-fiber")))
        for expected in ("go.mod", "main.go", "models/models.go", "handlers/handlers.go", "routes/routes.go", "Dockerfile"):
            assert expected in files

    def test_go_files_have_balanced_braces(self, blog_dsl_for):
        files = GoGenerator().generate(_parsed(blog_dsl_for("go-fiber")))
        for path, content in files.items():
            if path.endswith(".go"):
                _assert_balanced(content, path)

    def test_models_go_declares_every_model(self, blog_dsl_for):
        files = GoGenerator().generate(_parsed(blog_dsl_for("go-fiber")))
        models_go = files["models/models.go"]
        for model in ("User", "Post", "Comment", "Tag"):
            assert f"type {model} struct" in models_go

    def test_hashed_field_excluded_from_json(self, blog_dsl_for):
        files = GoGenerator().generate(_parsed(blog_dsl_for("go-fiber")))
        models_go = files["models/models.go"]
        # The `password` field is marked `hashed`; it must never round-trip
        # back out over JSON.
        password_line = next(line for line in models_go.splitlines() if "Password" in line and "struct" not in line)
        assert 'json:"-"' in password_line

    def test_routes_reference_defined_handlers(self, blog_dsl_for):
        files = GoGenerator().generate(_parsed(blog_dsl_for("go-fiber")))
        routes_go = files["routes/routes.go"]
        handlers_go = files["handlers/handlers.go"]
        for model in ("User", "Post", "Comment", "Tag"):
            for verb in ("List", "Create", "Get", "Update", "Delete"):
                fn = f"{verb}{model}"
                assert f"handlers.{fn}" in routes_go
                assert f"func {fn}(" in handlers_go


# -- Rails -------------------------------------------------------------


class TestRailsGenerator:
    def test_generates_bootable_skeleton(self, blog_dsl_for):
        files = RailsGenerator().generate(_parsed(blog_dsl_for("rails")))
        for expected in (
            "Gemfile",
            "config/routes.rb",
            "config/application.rb",
            "config/environment.rb",
            "config.ru",
            "bin/rails",
            "app/models/application_record.rb",
        ):
            assert expected in files

    def test_migration_order_respects_foreign_keys(self, blog_dsl_for):
        """Post references User; Comment references User, Post, and itself.
        User's migration must sort before Post's, and Post's before
        Comment's, or `add_foreign_key` targets a table that doesn't exist
        yet."""
        files = RailsGenerator().generate(_parsed(blog_dsl_for("rails")))
        migrations = sorted(f for f in files if f.startswith("db/migrate/") and "_create_" in f)

        def index_of(table_fragment):
            return next(i for i, f in enumerate(migrations) if table_fragment in f)

        assert index_of("create_users") < index_of("create_posts")
        assert index_of("create_posts") < index_of("create_comments")

    def test_join_table_migration_created_for_many_to_many(self, blog_dsl_for):
        files = RailsGenerator().generate(_parsed(blog_dsl_for("rails")))
        join_migrations = [f for f in files if f.startswith("db/migrate/") and "posts_tags" in f]
        assert len(join_migrations) == 1

    def test_no_double_pluralized_join_table_name(self, blog_dsl_for):
        files = RailsGenerator().generate(_parsed(blog_dsl_for("rails")))
        assert not any("tagses" in f or "postses" in f for f in files)

    def test_strong_params_hash_args_after_scalar_args(self, blog_dsl_for):
        """`params.require(:post).permit(:title, tag_ids: [])` is valid Ruby;
        `params.require(:post).permit(tag_ids: [], :title)` is a SyntaxError
        (bare hash args must trail positional args)."""
        files = RailsGenerator().generate(_parsed(blog_dsl_for("rails")))
        controller = files["app/controllers/api/v1/posts_controller.rb"]
        permit_line = next(line for line in controller.splitlines() if ".permit(" in line)
        args = permit_line.split(".permit(", 1)[1].rsplit(")", 1)[0]
        parts = [p.strip() for p in args.split(",")]
        seen_hash_arg = False
        for part in parts:
            is_hash_arg = ":" in part and not part.startswith(":")
            if is_hash_arg:
                seen_hash_arg = True
            elif seen_hash_arg:
                pytest.fail(f"scalar arg '{part}' appears after a hash arg in: {permit_line}")

    def test_has_secure_password_field_hashed_manually_not_via_digest_column(self, blog_dsl_for):
        """The DSL's `password` column is a plain `hashed` string field, not
        Rails' `password_digest` convention - `has_secure_password` would
        raise at runtime for a missing column, so the model must hash it
        itself instead."""
        files = RailsGenerator().generate(_parsed(blog_dsl_for("rails")))
        user_model = files["app/models/user.rb"]
        assert "has_secure_password" not in user_model
        assert "BCrypt::Password.create" in user_model

    def test_self_referential_fk_does_not_deadlock_ordering(self, blog_dsl_for):
        # Comment.parent -> Comment must not prevent Comment from ever being
        # scheduled (the topological sort must treat self-refs as free).
        files = RailsGenerator().generate(_parsed(blog_dsl_for("rails")))
        migrations = [f for f in files if "_create_comments.rb" in f]
        assert len(migrations) == 1
