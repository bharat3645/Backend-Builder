"""
Integration tests for core/app.py's Flask API, exercised via the real Flask
test client (no live server needed).
"""

import io
import json
import zipfile

import pytest


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "healthy"


class TestFrameworks:
    def test_lists_all_three_frameworks(self, client):
        resp = client.get("/api/v1/frameworks")
        assert resp.status_code == 200
        ids = {f["id"] for f in resp.get_json()["frameworks"]}
        assert ids == {"django", "go-fiber", "rails"}


class TestValidateDSL:
    def test_valid_spec(self, client, minimal_dsl):
        resp = client.post("/api/v1/validate-dsl", json={"dsl": minimal_dsl})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["valid"] is True
        assert body["errors"] == []

    def test_invalid_spec_returns_200_with_errors_not_a_crash(self, client):
        resp = client.post("/api/v1/validate-dsl", json={"dsl": {"meta": {}}})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["valid"] is False
        assert len(body["errors"]) > 0

    def test_missing_dsl_key_defaults_to_empty_and_reports_errors(self, client):
        resp = client.post("/api/v1/validate-dsl", json={})
        assert resp.status_code == 200
        assert resp.get_json()["valid"] is False


class TestParsePrompt:
    def test_empty_prompt_rejected(self, client):
        resp = client.post("/api/v1/parse-prompt", json={"prompt": ""})
        assert resp.status_code == 400

    def test_missing_prompt_key_rejected(self, client):
        resp = client.post("/api/v1/parse-prompt", json={})
        assert resp.status_code == 400

    def test_deterministic_fallback_used_without_api_keys(self, client, monkeypatch):
        # Make sure no real provider key leaks in from the host environment
        # and turns this into a live network call.
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        resp = client.post("/api/v1/parse-prompt", json={"prompt": "A blog with posts and comments"})
        assert resp.status_code == 200
        dsl = resp.get_json()["dsl"]
        assert "Post" in dsl["models"]
        assert "Comment" in dsl["models"]


class TestGenerateCode:
    @pytest.mark.parametrize("framework", ["django", "go-fiber", "rails"])
    def test_generate_json_for_each_framework(self, client, blog_dsl, framework):
        spec = dict(blog_dsl)
        spec["meta"] = {**spec["meta"], "framework": framework}
        resp = client.post("/api/v1/generate-code", json={"dsl": spec, "framework": framework})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["framework"] == framework
        assert body["file_count"] == len(body["files"])
        assert body["file_count"] > 0

    def test_generate_zip_download(self, client, blog_dsl):
        resp = client.post(
            "/api/v1/generate-code",
            json={"dsl": blog_dsl, "framework": "django", "format": "zip"},
        )
        assert resp.status_code == 200
        assert resp.mimetype == "application/zip"
        archive = zipfile.ZipFile(io.BytesIO(resp.data))
        assert archive.testzip() is None  # None means "no bad entries"
        assert len(archive.namelist()) > 0

    def test_zip_via_query_param(self, client, minimal_dsl):
        resp = client.post(
            "/api/v1/generate-code?format=zip",
            json={"dsl": minimal_dsl, "framework": "django"},
        )
        assert resp.status_code == 200
        assert resp.mimetype == "application/zip"

    def test_unsupported_framework_is_a_client_error(self, client, minimal_dsl):
        resp = client.post(
            "/api/v1/generate-code", json={"dsl": minimal_dsl, "framework": "spring-boot"}
        )
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_invalid_dsl_is_a_client_error_not_a_server_error(self, client):
        """A malformed spec is bad *input*, not a server fault - it should
        map to 400, not fall through to the generic 500 handler."""
        resp = client.post(
            "/api/v1/generate-code",
            json={"dsl": {"meta": {"name": "x", "version": "1", "framework": "django"}}, "framework": "django"},
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert "error" in body

    def test_malformed_json_body_is_a_client_error_not_a_server_error(self, client):
        resp = client.post(
            "/api/v1/generate-code",
            data="not json{{{",
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestAPIDocs:
    def test_openapi_spec_is_served_and_parses(self, client):
        import yaml

        resp = client.get("/openapi.yaml")
        assert resp.status_code == 200
        spec = yaml.safe_load(resp.data)
        assert spec["openapi"].startswith("3.")
        assert "/api/v1/generate-code" in spec["paths"]

    def test_docs_page_renders_swagger_ui(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert b"swagger-ui" in resp.data
        assert b"/openapi.yaml" in resp.data


class TestPreviewCode:
    def test_preview_lists_files_without_content(self, client, blog_dsl):
        resp = client.post("/api/v1/preview-code", json={"dsl": blog_dsl, "framework": "django"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["preview"]["file_count"] > 0
        for f in body["preview"]["files"]:
            assert "content" not in f
            assert {"path", "type", "description"} <= set(f.keys())

    def test_preview_invalid_framework_is_client_error(self, client, minimal_dsl):
        resp = client.post("/api/v1/preview-code", json={"dsl": minimal_dsl, "framework": "cobol"})
        assert resp.status_code == 400
