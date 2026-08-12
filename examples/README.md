# Example Generated Projects

These are real, verified outputs of the InfraNest generation engine (`core/generators/`)
from [`dsl/example_blog.yml`](../dsl/example_blog.yml) - a blog API with `User`, `Post`,
`Comment`, and `Tag` models. They're checked into the repo so you can see what InfraNest
actually produces without running the generator yourself.

| Directory | Framework | Verified with |
|---|---|---|
| [`blog-api-django/`](./blog-api-django) | Django + DRF | `python manage.py check` and `makemigrations` both pass cleanly |
| [`blog-api-go-fiber/`](./blog-api-go-fiber) | Go Fiber + GORM | `go build ./...` and `go vet ./...` both pass cleanly |
| [`blog-api-rails/`](./blog-api-rails) | Ruby on Rails (API-only) | Manually reviewed (no Ruby interpreter available in the generation environment) |

## Regenerating these

```bash
# with the core API running (see ../core/README or docker-compose.yml)
python ../copilot/copilot.py generate_code ../dsl/example_blog.yml --framework django --output blog-django.zip
python ../copilot/copilot.py generate_code ../dsl/example_blog.yml --framework go-fiber --output blog-go.zip
python ../copilot/copilot.py generate_code ../dsl/example_blog.yml --framework rails --output blog-rails.zip
```

Or from the web UI: **AI Prompt** / **DSL Builder** → **Generate Code** → pick a framework.
