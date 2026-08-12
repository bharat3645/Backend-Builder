<div align="center">
  <img src="./public/assets/logo.svg" width="72" height="72" alt="Backend Builder logo" />

  # Backend Builder

  **Describe a backend in plain English. Get a real, runnable one back.**

  Backend Builder turns a natural-language prompt (or a hand-written YAML spec)
  into a production-ready **Django + DRF**, **Go Fiber + GORM**, or **Ruby on
  Rails** backend project — models, serializers/views, migrations, auth, and
  Docker config included — through a web UI, a CLI, or a REST API.

  [![CI](https://github.com/bharat3645/Backend-Builder/actions/workflows/ci.yml/badge.svg)](https://github.com/bharat3645/Backend-Builder/actions/workflows/ci.yml)
  [![License: MIT](https://img.shields.io/github/license/bharat3645/Backend-Builder)](./LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](./core/requirements.txt)
  [![Node](https://img.shields.io/badge/node-20%2B-339933?logo=node.js&logoColor=white)](./package.json)
  [![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](./package.json)
  [![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](./tsconfig.json)

  [Quick Start](#-quick-start) · [Features](#-features) · [Architecture](#-architecture) · [Usage](#-usage) · [API Docs](#-api-documentation) · [Testing](#-testing)
</div>

> **Relationship to [InfraNest (PRISM)](https://github.com/bharat3645/prism-infranest):**
> both projects generate backend code from a DSL/natural-language prompt, but
> they are separate, independently-evolved codebases at different scope and
> maturity levels, not the same repo published twice. Backend Builder is the
> smaller, test-covered core engine (3 generators, a deterministic parser
> with optional OpenAI/Claude, a CLI, no accounts). InfraNest (PRISM) is a
> larger research-oriented platform layering multi-LLM follow-up-question
> generation, an evaluation/benchmarking subsystem, and an experimental local
> "intelligent analyzer" on top of a similar generation core. Pick this repo
> if you want a small, honestly-scoped generator you can read end to end;
> pick InfraNest (PRISM) if you want the larger feature surface.

---

## Overview

Bootstrapping a new backend service means writing the same models, CRUD
endpoints, auth wiring, and Docker config over and over — in whichever
framework the team happens to use. Backend Builder collapses that into one
step: describe the system once, in English or in a small declarative DSL, and
get a real project back for the framework you actually need.

```
"A blog API with users, posts, and comments. Users can register with
 email/password. Posts belong to a user and have a title, body, and
 published flag. Comments belong to a post and a user."
                              │
                              ▼
                    ┌───────────────────────┐
                    │  Backend Builder DSL   │   ← inspect / hand-edit before generating
                    └───────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         Django + DRF      Go Fiber        Ruby on Rails
        (models, serializers, views, urls, JWT auth, Dockerfile, migrations...)
```

This isn't a mockup — every code path above is real and covered by automated
tests (see [Testing](#-testing)), and `examples/` contains actual generator
output that's been checked with each framework's own toolchain.

## ✨ Features

**Generation engine**
- **Natural language → DSL**: turns a plain-English description into a
  structured backend spec, using GPT-4o or Claude when an API key is
  configured, and falling back to a deterministic keyword-based parser
  otherwise so the platform works with zero external dependencies
- **Visual DSL Builder**: inspect and hand-edit the generated specification
  in the UI before generating code
- **Multi-framework generation**: Django + DRF, Go Fiber + GORM, or Ruby on
  Rails from the same DSL — see [`examples/`](./examples) for real, verified
  output from each generator
- **Copilot CLI**: describe, preview, and generate backends from the terminal

**Quality & reliability**
- **74 backend pytest tests, 94% line coverage** — DSL validation rules,
  Django output verified with `ast.parse` for real syntax validity, Go output
  checked for balanced braces, Rails migrations checked for FK dependency
  ordering, every Flask endpoint hit through the real test client. See
  [`core/tests/`](./core/tests)
- **25 frontend Vitest tests** covering the API client's error handling and
  the Zustand stores' state transitions — see [`src/lib/*.test.ts`](./src/lib)
- **Real input validation & JSON error responses**: malformed DSL, an
  unsupported framework, or a non-JSON body returns a clean `400` with a
  `{"error": ...}` body instead of a generic `500`
- **CI on every push**: pytest with coverage, frontend lint/type-check/
  unit-tests/build, *and* a generator smoke test that produces a real project
  for all three frameworks and builds it with the actual toolchain
  (`manage.py check`, `go build && go vet`, `ruby -c`) — see
  [`.github/workflows/ci.yml`](./.github/workflows/ci.yml)
- **Interactive API docs**: full OpenAPI 3.0 spec, served with a self-hosted
  Swagger UI at `/docs`

**Platform**
- Docker Compose stack (frontend + core API + Postgres/Redis) for local dev
- Prometheus + Grafana dashboards scaffolded for the core API

## 🏗️ Architecture

```
Backend-Builder/
├── .github/workflows/        # CI: pytest, frontend build/lint/test, generator smoke-build
├── src/, index.html           # React + Vite frontend (the web UI)
│   ├── components/            # Navbar, Sidebar, Header
│   ├── pages/                 # Home, Dashboard
│   └── lib/                   # api.ts (HTTP client) + store.ts (Zustand), each with *.test.ts
├── core/                      # Flask code-generation engine (DSL -> project files)
│   ├── parsers/                # dsl_parser.py (validation) + agentic_parser.py (prompt -> DSL)
│   ├── generators/             # django_generator.py / go_generator.py / rails_generator.py
│   ├── scripts/                # generate_sample_projects.py - generate without a running server
│   ├── tests/                  # pytest suite for parsers, generators, and the API
│   └── openapi.yaml            # API spec, served at /openapi.yaml and /docs
├── templates/                 # Jinja2 templates used by the Django generator
├── dsl/                        # DSL specification + a full worked example
├── copilot/                    # Terminal client for the core API
├── examples/                   # Real generated output for all 3 frameworks, verified
├── monitoring/                 # Prometheus + Grafana config
└── docker-compose.yml           # Frontend + core API + Postgres/Redis/monitoring
```

**Request flow**: the React frontend (or the `copilot` CLI) talks to the
Flask core API over HTTP. A prompt goes through `AgenticParser` to become a
DSL spec; a DSL spec is checked by `DSLParser`; a validated spec is handed to
one of the three `*Generator` classes, which render either Jinja2 templates
(Django) or Python-built source (Go/Rails) into a project directory, zipped
and returned to the client.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS + Zustand |
| Generation engine | Python + Flask + Jinja2 |
| AI integration | OpenAI GPT-4o / Anthropic Claude (optional — see `core/.env.example`) |
| Testing | pytest + pytest-cov (backend), Vitest (frontend) |
| CI/CD | GitHub Actions |
| Deployment | Docker (`docker-compose.yml`, `Dockerfile.dev`, `core/Dockerfile`) |
| Monitoring | Prometheus + Grafana |
| Generated backends | Django + DRF, Go Fiber + GORM, Ruby on Rails |

## 🚀 Quick Start

### Prerequisites

- [Node.js](https://nodejs.org) 20+ and npm
- [Python](https://www.python.org) 3.11+
- (Optional) Docker + Docker Compose for the one-command setup
- (Optional) an OpenAI or Anthropic API key for LLM-backed prompt parsing —
  Backend Builder works without one, using a deterministic fallback parser

### Clone the repository

```bash
git clone https://github.com/bharat3645/Backend-Builder.git
cd Backend-Builder
```

### Run it locally

```bash
# 1. Frontend
npm install
cp .env.example .env
npm run dev                # http://localhost:5173

# 2. Core generation engine (separate terminal)
cd core
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # add OPENAI_API_KEY / ANTHROPIC_API_KEY here to enable LLM parsing
python app.py               # http://localhost:8000
```

### Or with Docker Compose

```bash
docker-compose up -d
```

## 📖 Usage

### Web UI

1. Start both the frontend and the core API (above).
2. Open `http://localhost:5173`, describe your backend in plain English (or
   start from a DSL file).
3. Review/edit the generated DSL spec in the **DSL Builder**.
4. Pick a framework and hit **Generate Code** to download a project zip.

### Copilot CLI

```bash
cd copilot
pip install -r requirements.txt

# Natural language -> DSL
python copilot.py describe_backend "A blog API with users, posts, and comments" --output blog.yml

# Generate a full project
python copilot.py generate_code blog.yml --framework django --output blog-api.zip

# Preview the file structure without downloading
python copilot.py preview_code blog.yml --framework go-fiber
```

### Core API directly

```bash
# Validate a DSL spec
curl -X POST http://localhost:8000/api/v1/validate-dsl \
  -H "Content-Type: application/json" \
  -d @dsl/example_blog.yml.json

# Generate a project (returns a zip)
curl -X POST http://localhost:8000/api/v1/generate-code \
  -H "Content-Type: application/json" \
  -d '{"dsl": <spec>, "framework": "django"}' \
  -o blog-api.zip
```

See [`dsl/README.md`](./dsl/README.md) for the full DSL schema and
[`dsl/example_blog.yml`](./dsl/example_blog.yml) for a complete worked
example.

## 📑 API Documentation

The core engine ships a full OpenAPI 3.0 spec ([`core/openapi.yaml`](./core/openapi.yaml))
with schemas for `DSLSpec`, `ValidationResult`, `GeneratedProject`, and every
error response. With the core API running:

- Interactive Swagger UI: `http://localhost:8000/docs`
- Raw spec: `http://localhost:8000/openapi.yaml`

## ✅ Testing

```bash
# Core generation engine - parser, all 3 generators, and the Flask API
cd core
pip install -r requirements.txt
pytest tests/ -v --cov=. --cov-report=term-missing

# Frontend - lib/api.ts and lib/store.ts
npm run test:run
```

| Suite | What it covers | Result |
|---|---|---|
| `core/tests/` (pytest) | DSL validation, Django/Go/Rails generators, every Flask endpoint, agentic parser fallback | 74 tests, 94% line coverage |
| `src/lib/*.test.ts` (Vitest) | API client error handling, Zustand store transitions | 25 tests |
| CI `generator-smoke` job | Generates a real project per framework and builds it with that ecosystem's own toolchain | `manage.py check`, `go build && go vet`, `ruby -c` all clean |

CI runs all of the above on every push — see
[`.github/workflows/ci.yml`](./.github/workflows/ci.yml) and
[`core/scripts/generate_sample_projects.py`](./core/scripts/generate_sample_projects.py).

## 🚦 Project Status

**What's real today**: prompt → DSL → generated code → downloadable project,
for all three frameworks, through both the web UI and the `copilot` CLI,
backed by real input validation and consistent JSON error responses.

**What's intentionally simulated** (so the UX can still be tried end to end
before the real infrastructure exists): cloud deployment, log aggregation,
and the Kafka-based event mesh that `docker-compose.yml` provisions but
nothing currently talks to. The `copilot` CLI's `deploy_project`, `view_logs`,
`run_audit`, and `simulate_api` commands are client-side simulations for the
same reason, and the web UI's **Deploy** page carries a visible "Simulated"
notice for the same reason - no cloud infrastructure is provisioned by
either. There are also no user accounts: `src/lib/store.ts` keeps your
projects in this browser's local storage only, since `core/app.py` has no
database or auth of its own.

## 📚 Further Documentation

- [DSL Specification](./dsl/README.md)
- [Template System](./templates/README.md)
- [Copilot CLI](./copilot/README.md)
- [Example generated projects](./examples/README.md)
- [OpenAPI spec source](./core/openapi.yaml) (interactive version at `/docs`)
- [InfraNest (PRISM)](https://github.com/bharat3645/prism-infranest) - a
  separate, larger platform covering similar ground (see the note at the top
  of this README for how the two relate)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes, add/run tests (`pytest core/tests` and `npm run test:run`)
4. Submit a pull request with a clear description

## 📄 License

Released under the [MIT License](./LICENSE) © 2026 [Bharat Singh Parihar](https://github.com/bharat3645).
