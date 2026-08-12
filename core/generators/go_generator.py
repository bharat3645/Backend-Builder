"""
Go Fiber + GORM code generator for Backend Builder.

Produces a runnable Go Fiber project (main.go, models, handlers, routes,
database bootstrap, Dockerfile) from a DSL specification.
"""

import re
from typing import Any, Dict, List, Tuple

from .base_generator import BaseGenerator

_GO_SCALAR_TYPES = {
    "string": "string",
    "text": "string",
    "integer": "int",
    "float": "float64",
    "boolean": "bool",
    "datetime": "time.Time",
    "date": "time.Time",
    "uuid": "string",
    "url": "string",
    "email": "string",
    "json": "string",
    "choice": "string",
}


def _pascal_case(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def _plural(name: str) -> str:
    lower = name.lower()
    return f"{lower}s"


class GoGenerator(BaseGenerator):
    """Generates a Go Fiber + GORM project from a DSL spec."""

    def generate(self, spec: Dict[str, Any]) -> Dict[str, str]:
        context = self.build_context(spec)
        module_name = context["meta"]["name"].replace("_", "-")
        module_path = f"github.com/backend-builder/{module_name}"

        files: Dict[str, str] = {}
        files["go.mod"] = self._go_mod(module_path)
        files["main.go"] = self._main_go(context)
        files["database/database.go"] = self._database_go(context)
        files["models/models.go"] = self._models_go(context)
        files["handlers/handlers.go"] = self._handlers_go(context, module_path)
        files["routes/routes.go"] = self._routes_go(context, module_path)
        files["Dockerfile"] = self._dockerfile(context)
        files[".env.example"] = self._env_example(context)
        files["README.md"] = self._readme(context)
        files[".dockerignore"] = "*.env\nbin/\n"

        return files

    # -- file builders --------------------------------------------------

    def _go_mod(self, module_path: str) -> str:
        return (
            f"module {module_path}\n\n"
            "go 1.21\n\n"
            "require (\n"
            "\tgithub.com/gofiber/fiber/v2 v2.52.15\n"
            "\tgorm.io/driver/postgres v1.5.9\n"
            "\tgorm.io/gorm v1.25.11\n"
            "\tgolang.org/x/crypto v0.28.0\n"
            "\tgithub.com/google/uuid v1.6.0\n"
            ")\n"
        )

    def _main_go(self, context: Dict[str, Any]) -> str:
        module = context["meta"]["name"].replace("-", "_")
        models = list(context.get("models", {}).keys())
        migrate_args = ", ".join(f"&models.{m}{{}}" for m in models) if models else ""
        return (
            "package main\n\n"
            "import (\n"
            "\t\"log\"\n"
            "\t\"os\"\n\n"
            "\t\"github.com/gofiber/fiber/v2\"\n"
            "\t\"github.com/gofiber/fiber/v2/middleware/cors\"\n"
            "\t\"github.com/gofiber/fiber/v2/middleware/logger\"\n"
            "\t\"github.com/gofiber/fiber/v2/middleware/recover\"\n\n"
            f"\t\"{self._module_path(context)}/database\"\n"
            f"\t\"{self._module_path(context)}/models\"\n"
            f"\t\"{self._module_path(context)}/routes\"\n"
            ")\n\n"
            "func main() {\n"
            "\tdb := database.Connect()\n\n"
            f"\tif err := db.AutoMigrate({migrate_args}); err != nil {{\n"
            "\t\tlog.Fatalf(\"failed to run migrations: %v\", err)\n"
            "\t}\n\n"
            "\tapp := fiber.New(fiber.Config{\n"
            f"\t\tAppName: \"{module}\",\n"
            "\t})\n\n"
            "\tapp.Use(logger.New())\n"
            "\tapp.Use(recover.New())\n"
            "\tapp.Use(cors.New())\n\n"
            "\tapp.Get(\"/health\", func(c *fiber.Ctx) error {\n"
            "\t\treturn c.JSON(fiber.Map{\"status\": \"healthy\"})\n"
            "\t})\n\n"
            "\troutes.Register(app, db)\n\n"
            "\tport := os.Getenv(\"PORT\")\n"
            "\tif port == \"\" {\n"
            "\t\tport = \"8000\"\n"
            "\t}\n\n"
            "\tlog.Fatal(app.Listen(\":\" + port))\n"
            "}\n"
        )

    def _module_path(self, context: Dict[str, Any]) -> str:
        module_name = context["meta"]["name"].replace("_", "-")
        return f"github.com/backend-builder/{module_name}"

    def _database_go(self, context: Dict[str, Any]) -> str:
        return (
            "package database\n\n"
            "import (\n"
            "\t\"log\"\n"
            "\t\"os\"\n\n"
            "\t\"gorm.io/driver/postgres\"\n"
            "\t\"gorm.io/gorm\"\n"
            ")\n\n"
            "// Connect opens a PostgreSQL connection using DATABASE_URL, falling back\n"
            "// to sensible local defaults for development.\n"
            "func Connect() *gorm.DB {\n"
            "\tdsn := os.Getenv(\"DATABASE_URL\")\n"
            "\tif dsn == \"\" {\n"
            "\t\tdsn = \"host=localhost user=postgres password=postgres dbname="
            f"{context['meta']['name'].replace('-', '_')} port=5432 sslmode=disable\"\n"
            "\t}\n\n"
            "\tdb, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})\n"
            "\tif err != nil {\n"
            "\t\tlog.Fatalf(\"failed to connect to database: %v\", err)\n"
            "\t}\n\n"
            "\treturn db\n"
            "}\n"
        )

    def _go_field(self, model_name: str, field_name: str, field_config: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        """Return a list of (go_name, go_type, tag) tuples for a DSL field."""
        go_name = _pascal_case(field_name)
        f_type = field_config.get("type", "string")

        if f_type == "foreign_key":
            related_model = field_config.get("model", "Model")
            id_field = (f"{go_name}ID", "string", f'gorm:"type:uuid" json:"{field_name}_id"')
            ptr_field = (
                go_name,
                f"*{related_model}",
                f'gorm:"foreignKey:{go_name}ID" json:"{field_name},omitempty"',
            )
            return [id_field, ptr_field]

        if f_type == "many_to_many":
            related_model = field_config.get("model", "Model")
            join_table = f"{model_name.lower()}_{field_name}"
            return [
                (
                    go_name,
                    f"[]{related_model}",
                    f'gorm:"many2many:{join_table};" json:"{field_name},omitempty"',
                )
            ]

        go_type = _GO_SCALAR_TYPES.get(f_type, "string")
        gorm_opts = []

        if field_config.get("primary_key"):
            gorm_opts.append("primaryKey")
            if f_type == "uuid":
                gorm_opts.append('type:uuid')
                gorm_opts.append("default:gen_random_uuid()")
        elif f_type == "uuid":
            gorm_opts.append("type:uuid")

        if field_config.get("unique"):
            gorm_opts.append("unique")
        if field_config.get("required") and not field_config.get("primary_key"):
            gorm_opts.append("not null")
        if field_config.get("max_length") and f_type == "string":
            gorm_opts.append(f"size:{field_config['max_length']}")
        if field_config.get("auto_now_add"):
            gorm_opts.append("autoCreateTime")
        if field_config.get("auto_now"):
            gorm_opts.append("autoUpdateTime")
        if "default" in field_config and f_type == "boolean":
            gorm_opts.append(f"default:{str(bool(field_config['default'])).lower()}")

        gorm_tag = ";".join(gorm_opts)
        tag = f'json:"{field_name}"'
        if gorm_tag:
            tag = f'gorm:"{gorm_tag}" {tag}'
        if field_config.get("hashed"):
            tag += ' json:"-"'

        return [(go_name, go_type, tag)]

    def _models_go(self, context: Dict[str, Any]) -> str:
        lines = [
            "package models",
            "",
            "import (",
            '\t"time"',
            ")",
            "",
        ]

        for model_name, model_config in context.get("models", {}).items():
            lines.append(f"type {model_name} struct {{")
            for field_name, field_config in model_config.get("fields", {}).items():
                for go_name, go_type, tag in self._go_field(model_name, field_name, field_config):
                    lines.append(f"\t{go_name} {go_type} `{tag}`")
            lines.append("}")
            lines.append("")
            lines.append(f"func ({model_name}) TableName() string {{ return \"{_plural(model_name.lower())}\" }}")
            lines.append("")

        return "\n".join(lines) + "\n"

    def _handlers_go(self, context: Dict[str, Any], module_path: str) -> str:
        lines = [
            "package handlers",
            "",
            "import (",
            '\t"github.com/gofiber/fiber/v2"',
            '\t"golang.org/x/crypto/bcrypt"',
            '\t"gorm.io/gorm"',
            "",
            f'\t"{module_path}/models"',
            ")",
            "",
        ]

        for model_name, model_config in context.get("models", {}).items():
            plural = _plural(model_name)
            fields = model_config.get("fields", {})
            hashed_fields = [f for f, cfg in fields.items() if cfg.get("hashed")]

            lines += [
                f"// List{model_name} returns every {model_name} record.",
                f"func List{model_name}(db *gorm.DB) fiber.Handler {{",
                "\treturn func(c *fiber.Ctx) error {",
                f"\t\tvar items []models.{model_name}",
                "\t\tif err := db.Find(&items).Error; err != nil {",
                "\t\t\treturn c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{\"error\": err.Error()})",
                "\t\t}",
                "\t\treturn c.JSON(items)",
                "\t}",
                "}",
                "",
                f"// Get{model_name} returns a single {model_name} by id.",
                f"func Get{model_name}(db *gorm.DB) fiber.Handler {{",
                "\treturn func(c *fiber.Ctx) error {",
                f"\t\tvar item models.{model_name}",
                "\t\tif err := db.First(&item, \"id = ?\", c.Params(\"id\")).Error; err != nil {",
                "\t\t\treturn c.Status(fiber.StatusNotFound).JSON(fiber.Map{\"error\": \"not found\"})",
                "\t\t}",
                "\t\treturn c.JSON(item)",
                "\t}",
                "}",
                "",
                f"// Create{model_name} creates a new {model_name}.",
                f"func Create{model_name}(db *gorm.DB) fiber.Handler {{",
                "\treturn func(c *fiber.Ctx) error {",
                f"\t\tvar item models.{model_name}",
                "\t\tif err := c.BodyParser(&item); err != nil {",
                "\t\t\treturn c.Status(fiber.StatusBadRequest).JSON(fiber.Map{\"error\": err.Error()})",
                "\t\t}",
            ]

            for hashed in hashed_fields:
                go_name = _pascal_case(hashed)
                lines += [
                    f"\t\tif item.{go_name} != \"\" {{",
                    f"\t\t\thashed, err := bcrypt.GenerateFromPassword([]byte(item.{go_name}), bcrypt.DefaultCost)",
                    "\t\t\tif err != nil {",
                    "\t\t\t\treturn c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{\"error\": \"failed to hash password\"})",
                    "\t\t\t}",
                    f"\t\t\titem.{go_name} = string(hashed)",
                    "\t\t}",
                ]

            lines += [
                "\t\tif err := db.Create(&item).Error; err != nil {",
                "\t\t\treturn c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{\"error\": err.Error()})",
                "\t\t}",
                "\t\treturn c.Status(fiber.StatusCreated).JSON(item)",
                "\t}",
                "}",
                "",
                f"// Update{model_name} updates an existing {model_name}.",
                f"func Update{model_name}(db *gorm.DB) fiber.Handler {{",
                "\treturn func(c *fiber.Ctx) error {",
                f"\t\tvar item models.{model_name}",
                "\t\tif err := db.First(&item, \"id = ?\", c.Params(\"id\")).Error; err != nil {",
                "\t\t\treturn c.Status(fiber.StatusNotFound).JSON(fiber.Map{\"error\": \"not found\"})",
                "\t\t}",
                f"\t\tvar updates models.{model_name}",
                "\t\tif err := c.BodyParser(&updates); err != nil {",
                "\t\t\treturn c.Status(fiber.StatusBadRequest).JSON(fiber.Map{\"error\": err.Error()})",
                "\t\t}",
                "\t\tif err := db.Model(&item).Updates(updates).Error; err != nil {",
                "\t\t\treturn c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{\"error\": err.Error()})",
                "\t\t}",
                "\t\treturn c.JSON(item)",
                "\t}",
                "}",
                "",
                f"// Delete{model_name} deletes a {model_name} by id.",
                f"func Delete{model_name}(db *gorm.DB) fiber.Handler {{",
                "\treturn func(c *fiber.Ctx) error {",
                f"\t\tif err := db.Delete(&models.{model_name}{{}}, \"id = ?\", c.Params(\"id\")).Error; err != nil {{",
                "\t\t\treturn c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{\"error\": err.Error()})",
                "\t\t}",
                "\t\treturn c.SendStatus(fiber.StatusNoContent)",
                "\t}",
                "}",
                "",
            ]
            # keep `plural` referenced so linting-by-eye stays sane even though
            # route registration (which uses it) lives in routes.go
            _ = plural

        return "\n".join(lines) + "\n"

    def _routes_go(self, context: Dict[str, Any], module_path: str) -> str:
        base_path = context["api"].get("base_path", "/api/v1")
        lines = [
            "package routes",
            "",
            "import (",
            '\t"github.com/gofiber/fiber/v2"',
            '\t"gorm.io/gorm"',
            "",
            f'\t"{module_path}/handlers"',
            ")",
            "",
            "// Register wires up REST routes for every model in the DSL spec.",
            "func Register(app *fiber.App, db *gorm.DB) {",
            f'\tapi := app.Group("{base_path}")',
            "",
        ]

        for model_name in context.get("models", {}).keys():
            plural = _plural(model_name)
            lines += [
                f'\tapi.Get("/{plural}", handlers.List{model_name}(db))',
                f'\tapi.Post("/{plural}", handlers.Create{model_name}(db))',
                f'\tapi.Get("/{plural}/:id", handlers.Get{model_name}(db))',
                f'\tapi.Put("/{plural}/:id", handlers.Update{model_name}(db))',
                f'\tapi.Delete("/{plural}/:id", handlers.Delete{model_name}(db))',
                "",
            ]

        lines.append("}")
        return "\n".join(lines) + "\n"

    def _dockerfile(self, context: Dict[str, Any]) -> str:
        port = context["deployment"]["docker"].get("port", 8000)
        return (
            "FROM golang:1.21-alpine AS build\n"
            "WORKDIR /app\n"
            "COPY go.mod ./\n"
            "RUN go mod download || true\n"
            "COPY . .\n"
            "RUN go build -o server .\n\n"
            "FROM alpine:3.19\n"
            "RUN apk add --no-cache ca-certificates\n"
            "WORKDIR /app\n"
            "COPY --from=build /app/server .\n"
            f"EXPOSE {port}\n"
            "HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- "
            f"http://localhost:{port}/health || exit 1\n"
            'CMD ["./server"]\n'
        )

    def _env_example(self, context: Dict[str, Any]) -> str:
        db_name = context["meta"]["name"].replace("-", "_")
        port = context["deployment"]["docker"].get("port", 8000)
        return (
            f"PORT={port}\n"
            f"DATABASE_URL=host=localhost user=postgres password=postgres dbname={db_name} port=5432 sslmode=disable\n"
        )

    def _readme(self, context: Dict[str, Any]) -> str:
        meta = context["meta"]
        return (
            f"# {meta['name']} (Go Fiber + GORM)\n\n"
            f"{meta.get('description', '')}\n\n"
            "Generated by [Backend Builder](https://github.com/bharat3645/Backend-Builder) from a DSL specification.\n\n"
            "## Setup\n\n"
            "```bash\n"
            "cp .env.example .env\n"
            "go mod tidy\n"
            "go run main.go\n"
            "```\n\n"
            "## Docker\n\n"
            "```bash\n"
            f"docker build -t {meta['name']} .\n"
            f"docker run -p {context['deployment']['docker'].get('port', 8000)}:{context['deployment']['docker'].get('port', 8000)} --env-file .env {meta['name']}\n"
            "```\n"
        )
