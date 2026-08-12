"""
InfraNest Core Generation Engine
Flask-based API for DSL parsing and code generation
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
import yaml
import os
import tempfile
import uuid
import zipfile
from datetime import datetime
import logging

from generators.django_generator import DjangoGenerator
from generators.go_generator import GoGenerator
from generators.rails_generator import RailsGenerator
from parsers.dsl_parser import DSLParser
from parsers.agentic_parser import AgenticParser

# Load environment variables from a local .env file if present (see .env.example)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=os.getenv('CORS_ORIGINS', '*').split(','))

# Initialize generators
generators = {
    'django': DjangoGenerator(),
    'go-fiber': GoGenerator(),
    'rails': RailsGenerator()
}

# Optional Prometheus metrics (scraped by monitoring/prometheus/prometheus.yml).
# Kept optional so the API still runs if the package isn't installed.
try:
    from prometheus_flask_exporter import PrometheusMetrics
    metrics = PrometheusMetrics(app)
    metrics.info('infranest_core_info', 'InfraNest core generation engine', version='1.0.0')
except ImportError:
    logger.warning('prometheus_flask_exporter not installed; /metrics endpoint disabled')


class APIError(Exception):
    """A client-input problem (bad DSL, unknown framework, malformed
    request, ...). Distinct from an unexpected server-side failure, so
    callers get an accurate status code instead of everything collapsing
    to 500."""

    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        payload = {'error': self.message}
        if self.details is not None:
            payload['details'] = self.details
        return payload


def json_body():
    """Parse the request body as JSON, raising a clean 400 APIError - rather
    than a raw 500 - for a missing/invalid/non-object body."""
    data = request.get_json(silent=True)
    if data is None:
        raise APIError('Request body must be valid JSON', 400)
    if not isinstance(data, dict):
        raise APIError('Request body must be a JSON object', 400)
    return data


@app.errorhandler(APIError)
def handle_api_error(err):
    logger.info(f"Rejected request: {err.message}")
    return jsonify(err.to_dict()), err.status_code


@app.errorhandler(HTTPException)
def handle_http_exception(err):
    # Preserve Werkzeug/Flask's own status code (404 for unknown routes,
    # 405 for a wrong HTTP verb, 415 for a non-JSON content type, etc.)
    # instead of letting a route's error handling downgrade it to 500.
    return jsonify({'error': err.description or err.name}), err.code


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    logger.exception("Unhandled server error")
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/v1/parse-prompt', methods=['POST'])
def parse_prompt():
    """Convert natural language prompt to DSL"""
    data = json_body()
    prompt = data.get('prompt', '')

    if not isinstance(prompt, str) or not prompt.strip():
        raise APIError('Prompt is required', 400)
    if len(prompt) > 4000:
        raise APIError('Prompt is too long (max 4000 characters)', 400)

    # Use agentic parser to convert prompt to DSL. Falls back to a
    # deterministic keyword-based DSL when no AI provider key is set.
    parser = AgenticParser(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
    )
    dsl_spec = parser.parse_prompt(prompt)

    return jsonify({
        'dsl': dsl_spec,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/validate-dsl', methods=['POST'])
def validate_dsl():
    """Validate DSL specification"""
    data = json_body()
    dsl_spec = data.get('dsl', {})
    if not isinstance(dsl_spec, dict):
        raise APIError("'dsl' must be a JSON object", 400)

    parser = DSLParser()
    validation_result = parser.validate(dsl_spec)

    return jsonify({
        'valid': validation_result['valid'],
        'errors': validation_result.get('errors', []),
        'warnings': validation_result.get('warnings', [])
    })

@app.route('/api/v1/generate-code', methods=['POST'])
def generate_code():
    """Generate backend code from DSL specification.

    Returns the generated files inline as JSON by default (used by the
    web UI's code viewer). Pass `"format": "zip"` in the request body, or
    `?format=zip` as a query param, to download a zip archive instead.
    """
    data = json_body()
    dsl_spec = data.get('dsl', {})
    framework = data.get('framework', 'django')
    response_format = data.get('format') or request.args.get('format', 'json')

    if not isinstance(dsl_spec, dict):
        raise APIError("'dsl' must be a JSON object", 400)
    if framework not in generators:
        raise APIError(
            f'Unsupported framework: {framework}',
            400,
            details={'supported': list(generators.keys())},
        )

    # Parse and validate DSL - a malformed spec is a client input problem
    # (400), not a server fault, so translate the parser's ValueError
    # instead of letting it fall through to the generic 500 handler.
    parser = DSLParser()
    try:
        parsed_spec = parser.parse(dsl_spec)
    except ValueError as e:
        raise APIError(str(e), 400) from e

    # Generate code
    generator = generators[framework]
    generated_files = generator.generate(parsed_spec)
    project_name = parsed_spec.get('meta', {}).get('name', 'project')

    if response_format == 'zip':
        # Create zip file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                for file_path, content in generated_files.items():
                    zip_file.writestr(file_path, content)

            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f"{project_name}-{framework}.zip",
                mimetype='application/zip'
            )

    return jsonify({
        'id': str(uuid.uuid4()),
        'project_name': project_name,
        'framework': framework,
        'files': generated_files,
        'file_count': len(generated_files),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/preview-code', methods=['POST'])
def preview_code():
    """Preview generated code structure without downloading"""
    data = json_body()
    dsl_spec = data.get('dsl', {})
    framework = data.get('framework', 'django')

    if not isinstance(dsl_spec, dict):
        raise APIError("'dsl' must be a JSON object", 400)
    if framework not in generators:
        raise APIError(
            f'Unsupported framework: {framework}',
            400,
            details={'supported': list(generators.keys())},
        )

    parser = DSLParser()
    try:
        parsed_spec = parser.parse(dsl_spec)
    except ValueError as e:
        raise APIError(str(e), 400) from e

    generator = generators[framework]
    preview = generator.preview(parsed_spec)

    return jsonify({
        'preview': preview,
        'framework': framework,
        'project_name': parsed_spec.get('meta', {}).get('name', 'project')
    })

@app.route('/api/v1/frameworks', methods=['GET'])
def get_frameworks():
    """Get list of supported frameworks"""
    return jsonify({
        'frameworks': [
            {
                'id': 'django',
                'name': 'Django + DRF',
                'description': 'Python web framework with Django REST Framework',
                'language': 'Python',
                'features': ['ORM', 'Admin Panel', 'Authentication', 'REST API']
            },
            {
                'id': 'go-fiber',
                'name': 'Go Fiber + GORM',
                'description': 'High-performance Go web framework with GORM ORM',
                'language': 'Go',
                'features': ['High Performance', 'ORM', 'Middleware', 'REST API']
            },
            {
                'id': 'rails',
                'name': 'Ruby on Rails',
                'description': 'Convention over configuration web framework',
                'language': 'Ruby',
                'features': ['ActiveRecord', 'Scaffolding', 'Authentication', 'REST API']
            }
        ]
    })

_OPENAPI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openapi.yaml')


@app.route('/openapi.yaml', methods=['GET'])
def openapi_spec():
    """Serve the raw OpenAPI 3.0 specification for this API."""
    if not os.path.exists(_OPENAPI_PATH):
        raise APIError('openapi.yaml is missing from the deployment', 404)
    return send_file(_OPENAPI_PATH, mimetype='application/yaml')


@app.route('/docs', methods=['GET'])
def api_docs():
    """Interactive Swagger UI for /openapi.yaml."""
    html = """<!doctype html>
<html>
<head>
  <title>InfraNest API Docs</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
  <style>body { margin: 0; background: #1a1a2e; }</style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      url: '/openapi.yaml',
      dom_id: '#swagger-ui',
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    });
  </script>
</body>
</html>"""
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

if __name__ == '__main__':
    # Debug mode (verbose tracebacks + the Werkzeug interactive debugger)
    # must be opt-in, not the default - it's meant for local development
    # only. Set FLASK_DEBUG=1 in core/.env for that; leave it unset in any
    # deployed environment.
    debug_mode = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=8000, debug=debug_mode)