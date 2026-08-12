"""
Agentic Parser for InfraNest
Converts natural language prompts to DSL specifications, optionally using
an LLM (OpenAI or Anthropic) when an API key is configured. Falls back to a
deterministic, keyword-based DSL generator so the platform is fully usable
without any AI provider configured.
"""

import json
import logging
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert backend architect. Convert natural language descriptions into InfraNest DSL specifications.

Generate valid YAML that follows the InfraNest DSL schema:

- meta: Project metadata (name, version, framework, database)
- auth: Authentication configuration
- models: Data models with fields, types, and relationships
- api: REST API endpoints with handlers and permissions
- jobs: Background jobs and triggers
- deployment: Docker and scaling configuration

Focus on:
1. Proper field types and relationships
2. Sensible permissions and security
3. RESTful API design
4. Common patterns and best practices

Return only valid YAML without explanations or markdown code fences."""


class AgenticParser:
    """AI-powered parser for converting natural language to DSL"""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        # `api_key` kept for backwards compatibility with earlier callers;
        # it is treated as an OpenAI key.
        self.openai_api_key = openai_api_key or api_key
        self.anthropic_api_key = anthropic_api_key

    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Convert natural language prompt to DSL specification"""

        if self.openai_api_key:
            dsl = self._parse_with_openai(prompt)
            if dsl:
                return dsl

        if self.anthropic_api_key:
            dsl = self._parse_with_anthropic(prompt)
            if dsl:
                return dsl

        # No provider configured (or the call failed) - use the
        # deterministic keyword-based generator so the app stays usable.
        return self._generate_mock_dsl(prompt)

    # -- AI-backed generation ------------------------------------------------

    def _parse_with_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content
            return self._coerce_to_dsl(content)
        except Exception as exc:  # pragma: no cover - network/SDK dependent
            logger.warning("OpenAI DSL generation failed, falling back: %s", exc)
            return None

    def _parse_with_anthropic(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            content = "".join(
                block.text for block in response.content if getattr(block, "type", None) == "text"
            )
            return self._coerce_to_dsl(content)
        except Exception as exc:  # pragma: no cover - network/SDK dependent
            logger.warning("Anthropic DSL generation failed, falling back: %s", exc)
            return None

    def _coerce_to_dsl(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse a model response (YAML or JSON, possibly fenced) into a dict."""
        if not content:
            return None

        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            # Drop a leading language hint like "yaml\n" or "json\n"
            if "\n" in cleaned:
                first_line, rest = cleaned.split("\n", 1)
                if first_line.strip().lower() in ("yaml", "yml", "json"):
                    cleaned = rest

        try:
            parsed = yaml.safe_load(cleaned)
        except yaml.YAMLError:
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError:
                logger.warning("Model response was not valid YAML or JSON")
                return None

        if not isinstance(parsed, dict):
            return None
        return parsed

    # -- Deterministic fallback -----------------------------------------------

    def _generate_mock_dsl(self, prompt: str) -> Dict[str, Any]:
        """Generate mock DSL based on prompt keywords"""

        # Extract project name from prompt
        project_name = self._extract_project_name(prompt)

        # Detect models based on keywords
        models = self._detect_models(prompt)

        # Generate basic DSL structure
        dsl = {
            'meta': {
                'name': project_name,
                'description': f'API generated from: {prompt[:100]}...',
                'version': '1.0.0',
                'framework': 'django',
                'database': 'postgresql'
            },
            'auth': {
                'provider': 'jwt',
                'user_model': 'User',
                'required_fields': ['email', 'password']
            },
            'models': models,
            'api': {
                'base_path': '/api/v1',
                'endpoints': self._generate_endpoints(models)
            },
            'deployment': {
                'docker': {
                    'port': 8000,
                    'health_check': '/health'
                }
            }
        }

        return dsl

    def _extract_project_name(self, prompt: str) -> str:
        """Extract project name from prompt"""
        # Simple keyword-based extraction
        keywords = ['blog', 'shop', 'store', 'forum', 'social', 'task', 'todo', 'project']

        for keyword in keywords:
            if keyword in prompt.lower():
                return f"{keyword}-api"

        return "api-project"

    def _detect_models(self, prompt: str) -> Dict[str, Any]:
        """Detect models from prompt keywords"""
        models = {}

        # Always include User model
        models['User'] = {
            'fields': {
                'id': {'type': 'uuid', 'primary_key': True, 'auto_generated': True},
                'email': {'type': 'string', 'unique': True, 'required': True},
                'password': {'type': 'string', 'required': True, 'hashed': True},
                'first_name': {'type': 'string', 'max_length': 100},
                'last_name': {'type': 'string', 'max_length': 100},
                'created_at': {'type': 'datetime', 'auto_now_add': True}
            },
            'permissions': {
                'read': ['owner', 'admin'],
                'write': ['owner', 'admin'],
                'create': ['authenticated'],
                'delete': ['owner', 'admin']
            }
        }

        # Detect common model patterns
        if any(word in prompt.lower() for word in ['blog', 'post', 'article']):
            models['Post'] = {
                'fields': {
                    'id': {'type': 'uuid', 'primary_key': True, 'auto_generated': True},
                    'title': {'type': 'string', 'required': True, 'max_length': 200},
                    'content': {'type': 'text', 'required': True},
                    'author': {'type': 'foreign_key', 'model': 'User', 'on_delete': 'cascade'},
                    'published': {'type': 'boolean', 'default': False},
                    'created_at': {'type': 'datetime', 'auto_now_add': True}
                },
                'permissions': {
                    'read': ['public'],
                    'write': ['owner', 'admin'],
                    'create': ['authenticated'],
                    'delete': ['owner', 'admin']
                }
            }

        if any(word in prompt.lower() for word in ['comment', 'reply']):
            models['Comment'] = {
                'fields': {
                    'id': {'type': 'uuid', 'primary_key': True, 'auto_generated': True},
                    'content': {'type': 'text', 'required': True},
                    'author': {'type': 'foreign_key', 'model': 'User', 'on_delete': 'cascade'},
                    'post': {'type': 'foreign_key', 'model': 'Post', 'on_delete': 'cascade'},
                    'created_at': {'type': 'datetime', 'auto_now_add': True}
                },
                'permissions': {
                    'read': ['public'],
                    'write': ['owner', 'admin'],
                    'create': ['authenticated'],
                    'delete': ['owner', 'admin']
                }
            }

        if any(word in prompt.lower() for word in ['product', 'item', 'shop', 'store']):
            models['Product'] = {
                'fields': {
                    'id': {'type': 'uuid', 'primary_key': True, 'auto_generated': True},
                    'name': {'type': 'string', 'required': True, 'max_length': 200},
                    'description': {'type': 'text'},
                    'price': {'type': 'float', 'required': True},
                    'stock': {'type': 'integer', 'default': 0},
                    'created_at': {'type': 'datetime', 'auto_now_add': True}
                },
                'permissions': {
                    'read': ['public'],
                    'write': ['admin'],
                    'create': ['admin'],
                    'delete': ['admin']
                }
            }

        return models

    def _generate_endpoints(self, models: Dict[str, Any]) -> list:
        """Generate API endpoints for models"""
        endpoints = []

        # Authentication endpoints
        endpoints.extend([
            {'path': '/auth/register', 'method': 'POST', 'handler': 'auth.register', 'public': True},
            {'path': '/auth/login', 'method': 'POST', 'handler': 'auth.login', 'public': True},
            {'path': '/auth/logout', 'method': 'POST', 'handler': 'auth.logout', 'auth_required': True}
        ])

        # Generate CRUD endpoints for each model
        for model_name in models.keys():
            model_lower = model_name.lower()
            model_plural = f"{model_lower}s"  # Simple pluralization

            endpoints.extend([
                {'path': f'/{model_plural}', 'method': 'GET', 'handler': f'{model_plural}.list', 'public': True},
                {'path': f'/{model_plural}', 'method': 'POST', 'handler': f'{model_plural}.create', 'auth_required': True},
                {'path': f'/{model_plural}/{{id}}', 'method': 'GET', 'handler': f'{model_plural}.retrieve', 'public': True},
                {'path': f'/{model_plural}/{{id}}', 'method': 'PUT', 'handler': f'{model_plural}.update', 'auth_required': True},
                {'path': f'/{model_plural}/{{id}}', 'method': 'DELETE', 'handler': f'{model_plural}.delete', 'auth_required': True}
            ])

        return endpoints
