# Template System

`core/generators/` turns a validated DSL specification into a full backend
project. Frameworks generate code two different ways:

## Django (`templates/django/*.j2`)

Django's models/serializers/views/urls come from real Jinja2 templates in
this directory, rendered by `core/generators/django_generator.py`. The
project scaffolding around them (`settings.py`, `manage.py`, `wsgi.py`,
`admin.py`, `.env.example`, `README.md`, etc.) is generated directly in
Python, since it doesn't vary per-model the way the DRF layer does.

## Go Fiber and Ruby on Rails

These frameworks don't have `.j2` template files - `core/generators/go_generator.py`
and `core/generators/rails_generator.py` build the project (Fiber handlers +
GORM models, or Rails controllers/models/migrations) directly in Python.
This was a deliberate tradeoff: the GORM struct tags, migration ordering
(models must be created before anything that adds a `foreign_key:` to them),
and Rails' strong-params/association-name conventions all needed enough
conditional logic that plain Jinja2 templates became harder to get right
than generating the code directly.

Adding `.j2` templates for these frameworks (mirroring the Django layout) is
a reasonable next step if the per-field logic stays simple - see
`django_generator.py` for the pattern to follow.

## Adding a new field type or framework

1. Add the type to `DSLParser.field_types` in `core/parsers/dsl_parser.py`.
2. Handle it in each generator's field-rendering logic
   (`_go_field` in `go_generator.py`, the Jinja `{% if field_config.type == ... %}`
   chain in `models.py.j2` for Django, the `_MIGRATION_TYPES` map in
   `rails_generator.py`).
3. Regenerate `examples/` (see `examples/README.md`) and re-verify:
   Django with `manage.py check`, Go with `go build ./... && go vet ./...`.

See [`../dsl/README.md`](../dsl/README.md) for the DSL schema itself.
