"""
Tests for parsers/dsl_parser.py.
"""

import copy

import pytest

from parsers.dsl_parser import DSLParser


class TestValidate:
    def test_minimal_spec_is_valid(self, minimal_dsl):
        result = DSLParser().validate(minimal_dsl)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_blog_spec_is_valid(self, blog_dsl):
        result = DSLParser().validate(blog_dsl)
        assert result["valid"] is True, result["errors"]

    def test_missing_required_sections(self):
        result = DSLParser().validate({})
        assert result["valid"] is False
        assert any("meta" in e for e in result["errors"])
        assert any("models" in e for e in result["errors"])

    def test_missing_meta_fields(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        del spec["meta"]["version"]
        del spec["meta"]["framework"]
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("version" in e for e in result["errors"])
        assert any("framework" in e for e in result["errors"])

    def test_unsupported_framework_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["meta"]["framework"] = "spring-boot"
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("Unsupported framework" in e for e in result["errors"])

    @pytest.mark.parametrize("framework", ["django", "go-fiber", "rails"])
    def test_all_supported_frameworks_accepted(self, minimal_dsl, framework):
        spec = copy.deepcopy(minimal_dsl)
        spec["meta"]["framework"] = framework
        result = DSLParser().validate(spec)
        assert result["valid"] is True, result["errors"]

    def test_invalid_project_name_format_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["meta"]["name"] = "My Cool API!"
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("Project name" in e for e in result["errors"])

    def test_model_name_must_be_pascal_case(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["widget"] = spec["models"].pop("Widget")
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("widget" in e and "uppercase" in e for e in result["errors"])

    def test_model_without_fields_section_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["Widget"] = {}
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("must have a 'fields' section" in e for e in result["errors"])

    def test_field_without_type_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["Widget"]["fields"]["mystery"] = {}
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("must have a 'type'" in e for e in result["errors"])

    def test_invalid_field_type_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["Widget"]["fields"]["odd"] = {"type": "binary_blob"}
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("Invalid field type" in e for e in result["errors"])

    def test_no_primary_key_warns_not_errors(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["Widget"]["fields"]["id"]["primary_key"] = False
        result = DSLParser().validate(spec)
        assert result["valid"] is True
        assert any("no primary key" in w for w in result["warnings"])

    def test_multiple_primary_keys_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["Widget"]["fields"]["name"]["primary_key"] = True
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("multiple primary keys" in e for e in result["errors"])

    def test_auth_missing_provider_gives_single_clear_error(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["auth"] = {}
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        auth_errors = [e for e in result["errors"] if "auth" in e.lower() or "provider" in e.lower()]
        # Omitting `provider` entirely should not *also* be reported as
        # "Unsupported auth provider: None" - that's a confusing duplicate
        # of the same underlying problem.
        assert len(auth_errors) == 1
        assert "must specify a 'provider'" in auth_errors[0]

    def test_auth_unsupported_provider_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["auth"] = {"provider": "basic-auth"}
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("Unsupported auth provider" in e for e in result["errors"])

    def test_api_endpoint_missing_fields_rejected(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["api"] = {"endpoints": [{"path": "/widgets"}]}
        result = DSLParser().validate(spec)
        assert result["valid"] is False
        assert any("method" in e for e in result["errors"])
        assert any("handler" in e for e in result["errors"])


class TestSanitizeKeys:
    def test_unquoted_null_key_becomes_string(self):
        # PyYAML parses an unquoted `null: true` mapping key as Python
        # `None`, not the string "null" - this is exactly the bug that was
        # in dsl/example_blog.yml (`published_at: {type: datetime, null: true}`).
        spec = {"models": {"Post": {"fields": {"x": {"type": "datetime", None: True}}}}}
        sanitized = DSLParser()._sanitize_keys(spec)
        field = sanitized["models"]["Post"]["fields"]["x"]
        assert None not in field
        assert field["null"] is True

    def test_bool_key_becomes_string(self):
        spec = {True: "yes", False: "no"}
        sanitized = DSLParser()._sanitize_keys(spec)
        assert sanitized == {"true": "yes", "false": "no"}

    def test_sanitize_is_json_serializable(self):
        import json

        spec = {"models": {"Post": {"fields": {"x": {None: True, 1: "int-key"}}}}}
        sanitized = DSLParser()._sanitize_keys(spec)
        json.dumps(sanitized)  # must not raise


class TestParse:
    def test_parse_raises_on_invalid_spec(self):
        with pytest.raises(ValueError):
            DSLParser().parse({})

    def test_parse_normalizes_missing_primary_key(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["Widget"]["fields"]["id"]["primary_key"] = False
        del spec["models"]["Widget"]["fields"]["id"]

        parsed = DSLParser().parse(spec)
        fields = parsed["models"]["Widget"]["fields"]
        assert "id" in fields
        assert fields["id"]["primary_key"] is True

    def test_parse_sanitizes_null_key_end_to_end(self, minimal_dsl):
        spec = copy.deepcopy(minimal_dsl)
        spec["models"]["Widget"]["fields"]["archived_at"] = {"type": "datetime", None: True}
        parsed = DSLParser().parse(spec)
        field = parsed["models"]["Widget"]["fields"]["archived_at"]
        assert field["null"] is True
