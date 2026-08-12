# Backend Builder DSL Specification

The Backend Builder DSL (Domain Specific Language) provides a declarative way to describe backend systems that can be converted into production-ready code across multiple frameworks.

## Structure

### Meta Information
```yaml
meta:
  name: "project-name"
  description: "Project description"
  version: "1.0.0"
  framework: "django"  # django, go-fiber, rails
  database: "postgresql"
```

### Authentication
```yaml
auth:
  provider: "jwt"  # jwt, oauth2, custom
  user_model: "User"
  required_fields: ["email", "password"]
  optional_fields: ["first_name", "last_name"]
```

### Models
Define your data models with fields, relationships, and permissions:
```yaml
models:
  User:
    fields:
      id:
        type: "uuid"
        primary_key: true
      email:
        type: "string"
        unique: true
        required: true
    permissions:
      read: ["owner", "admin"]
      write: ["owner", "admin"]
```

### API Endpoints
Define RESTful API endpoints with automatic CRUD generation:
```yaml
api:
  base_path: "/api/v1"
  endpoints:
    - path: "/users"
      method: "GET"
      handler: "users.list"
      auth_required: true
```

### Background Jobs
Define async jobs triggered by events:
```yaml
jobs:
  - name: "send_welcome_email"
    trigger: "user.created"
    handler: "jobs.send_welcome_email"
    retry_count: 3
```

### Deployment Configuration
Specify deployment requirements:
```yaml
deployment:
  docker:
    port: 8000
    health_check: "/health"
  scaling:
    min_instances: 2
    max_instances: 10
```

## Field Types

- `string`: Text field with optional max_length
- `text`: Long text field
- `integer`: Numeric field
- `float`: Decimal field
- `boolean`: True/False field
- `datetime`: Date and time field
- `date`: Date only field
- `uuid`: Unique identifier
- `url`: URL field
- `email`: Email field
- `json`: JSON data field
- `foreign_key`: Reference to another model
- `many_to_many`: Many-to-many relationship
- `choice`: Field with predefined choices

## Permissions

- `public`: Available to everyone
- `authenticated`: Available to logged-in users
- `owner`: Available to the resource owner
- `admin`: Available to administrators
- `custom`: Custom permission logic

## A YAML gotcha to watch for

If you write a field property literally named `null` (e.g. to mean
"this foreign key is nullable"), quote the key: `"null": true`. YAML parses
an unquoted `null:` as the null/`None` key rather than the string `"null"`,
which silently breaks the property lookup (and can crash JSON serialization
of the spec). Backend Builder's parser normalizes this defensively, but generators
that expect a string key `"null"` still won't see it if it comes through
as an actual `None` upstream of the parser.

## Examples

See `example_blog.yml` for a complete blog API specification.