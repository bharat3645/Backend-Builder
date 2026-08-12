"""
Ruby on Rails code generator for InfraNest.

Produces a Rails API project (models, controllers, routes, migrations,
Gemfile, Dockerfile) from a DSL specification.
"""

import datetime
import re
from typing import Any, Dict, List

from .base_generator import BaseGenerator

_MIGRATION_TYPES = {
    "string": "string",
    "text": "text",
    "integer": "integer",
    "float": "float",
    "boolean": "boolean",
    "datetime": "datetime",
    "date": "date",
    "uuid": "uuid",
    "url": "string",
    "email": "string",
    "json": "jsonb",
    "choice": "string",
}


def _snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _plural(name: str) -> str:
    lower = name.lower()
    if lower.endswith("s"):
        return lower  # assume already plural - avoid "tags" -> "tagses"
    if lower.endswith("y") and lower[-2:-1] not in "aeiou":
        return lower[:-1] + "ies"
    if lower.endswith(("sh", "ch", "x", "z")):
        return lower + "es"
    return lower + "s"


def _camelize(name: str) -> str:
    """snake_case (possibly multi-word) -> PascalCase, matching the class
    name Rails' Zeitwerk autoloader (and the migration loader) expect for
    a given underscored file/table name."""
    return "".join(part[:1].upper() + part[1:] for part in name.split("_") if part)


class RailsGenerator(BaseGenerator):
    """Generates a Ruby on Rails API project from a DSL spec."""

    def generate(self, spec: Dict[str, Any]) -> Dict[str, str]:
        context = self.build_context(spec)
        models = context.get("models", {})
        reverse_associations = self._reverse_associations(models)
        migration_order = self._topological_order(models)

        module_name = _camelize(context["meta"]["name"].replace("-", "_"))

        files: Dict[str, str] = {}
        files["Gemfile"] = self._gemfile(context)
        files["config/routes.rb"] = self._routes_rb(context)
        files["config/database.yml"] = self._database_yml(context)
        files["Dockerfile"] = self._dockerfile(context)
        files[".env.example"] = self._env_example(context)
        files["README.md"] = self._readme(context)
        files["app/controllers/application_controller.rb"] = self._application_controller()
        files["app/models/application_record.rb"] = (
            "class ApplicationRecord < ActiveRecord::Base\n"
            "  primary_abstract_class\n"
            "end\n"
        )
        files[".dockerignore"] = "log/\ntmp/\n.env\n"
        files[".ruby-version"] = "3.2.2\n"

        # Minimal-but-bootable Rails application skeleton. Without these,
        # `bin/rails` doesn't exist and `rails server` has nothing to boot.
        files["config.ru"] = (
            "require_relative 'config/environment'\n\n"
            "run Rails.application\n"
            "Rails.application.load_server\n"
        )
        files["config/boot.rb"] = (
            "ENV['BUNDLE_GEMFILE'] ||= File.expand_path('../Gemfile', __dir__)\n\n"
            "require 'bundler/setup'\n"
            "require 'bootsnap/setup' if File.exist?(File.expand_path('../Gemfile.lock', __dir__))\n"
        )
        files["config/application.rb"] = (
            "require_relative 'boot'\n\n"
            "require 'rails/all'\n\n"
            "Bundler.require(*Rails.groups)\n\n"
            f"module {module_name}\n"
            "  class Application < Rails::Application\n"
            "    config.load_defaults 7.1\n"
            "    config.api_only = true\n"
            "  end\n"
            "end\n"
        )
        files["config/environment.rb"] = (
            "require_relative 'application'\n\n"
            "Rails.application.initialize!\n"
        )
        files["config/puma.rb"] = (
            'max_threads_count = ENV.fetch("RAILS_MAX_THREADS") { 5 }\n'
            "min_threads_count = ENV.fetch(\"RAILS_MIN_THREADS\") { max_threads_count }\n"
            "threads min_threads_count, max_threads_count\n\n"
            f'port ENV.fetch("PORT") {{ {context["deployment"]["docker"].get("port", 3000)} }}\n\n'
            'environment ENV.fetch("RAILS_ENV") { "development" }\n\n'
            "pidfile ENV.fetch(\"PIDFILE\") { \"tmp/pids/server.pid\" }\n"
        )
        files["config/environments/development.rb"] = (
            "Rails.application.configure do\n"
            "  config.cache_classes = false\n"
            "  config.eager_load = false\n"
            "  config.consider_all_requests_local = true\n"
            "  config.active_support.deprecation = :log\n"
            "end\n"
        )
        files["config/environments/test.rb"] = (
            "Rails.application.configure do\n"
            "  config.cache_classes = true\n"
            "  config.eager_load = false\n"
            "  config.active_support.deprecation = :stderr\n"
            "end\n"
        )
        files["config/environments/production.rb"] = (
            "Rails.application.configure do\n"
            "  config.cache_classes = true\n"
            "  config.eager_load = true\n"
            "  config.consider_all_requests_local = false\n"
            "  config.log_level = :info\n"
            "  config.force_ssl = ENV.fetch('FORCE_SSL', 'true') == 'true'\n"
            "end\n"
        )
        files["config/initializers/cors.rb"] = (
            "Rails.application.config.middleware.insert_before 0, Rack::Cors do\n"
            "  allow do\n"
            "    origins ENV.fetch('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')\n\n"
            "    resource '*',\n"
            "      headers: :any,\n"
            "      methods: [:get, :post, :put, :patch, :delete, :options, :head]\n"
            "  end\n"
            "end\n"
        )
        files["bin/rails"] = (
            "#!/usr/bin/env ruby\n"
            "APP_PATH = File.expand_path('../config/application', __dir__)\n"
            "require_relative '../config/boot'\n"
            "require 'rails/commands'\n"
        )

        base_time = datetime.datetime(2024, 1, 1)
        for model_name, model_config in models.items():
            table = _plural(_snake(model_name))

            files[f"app/models/{_snake(model_name)}.rb"] = self._model_rb(
                model_name, model_config, context, reverse_associations.get(model_name, [])
            )
            files[f"app/controllers/api/v1/{table}_controller.rb"] = self._controller_rb(
                model_name, model_config, context
            )

        # Migrations must be timestamped in dependency order (a table can
        # only add a `foreign_key:` constraint to a table that already
        # exists), which may differ from the order models were declared in
        # the DSL.
        index = 0
        for model_name in migration_order:
            table = _plural(_snake(model_name))
            timestamp = (base_time + datetime.timedelta(minutes=index)).strftime("%Y%m%d%H%M%S")
            files[f"db/migrate/{timestamp}_create_{table}.rb"] = self._migration_rb(
                model_name, models[model_name]
            )
            index += 1

        # Every has_and_belongs_to_many association declared on a model
        # needs a join table migration, or the association raises
        # "relation does not exist" the first time it's used.
        for join_table, (left_table, right_table) in self._join_tables(models).items():
            timestamp = (base_time + datetime.timedelta(minutes=index)).strftime("%Y%m%d%H%M%S")
            files[f"db/migrate/{timestamp}_create_{join_table}.rb"] = self._join_migration_rb(
                join_table, left_table, right_table
            )
            index += 1

        return files

    def _join_tables(self, models: Dict[str, Any]) -> Dict[str, tuple]:
        """Collect unique join tables needed for many_to_many fields, mapping
        join_table_name -> (left_table, right_table)."""
        joins: Dict[str, tuple] = {}
        for model_name, model_config in models.items():
            for field_config in model_config.get("fields", {}).values():
                if field_config.get("type") != "many_to_many":
                    continue
                target = field_config.get("model")
                if not target or target not in models:
                    continue
                left_table = _plural(_snake(model_name))
                right_table = _plural(_snake(target))
                join_table = self._join_table(model_name, target)
                joins.setdefault(join_table, (left_table, right_table))
        return joins

    # -- dependency ordering -------------------------------------------

    def _topological_order(self, models: Dict[str, Any]) -> List[str]:
        """Order models so a referenced model's migration always precedes
        any migration that adds a foreign key to it (self-references are
        fine, since the constraint is added after the table already
        exists within the same migration)."""
        deps: Dict[str, List[str]] = {name: [] for name in models}
        for model_name, model_config in models.items():
            for field_config in model_config.get("fields", {}).values():
                if field_config.get("type") == "foreign_key":
                    target = field_config.get("model")
                    if target in models and target != model_name:
                        deps[model_name].append(target)

        ordered: List[str] = []
        visited: Dict[str, str] = {}  # name -> 'visiting' | 'done'

        def visit(name: str) -> None:
            state = visited.get(name)
            if state == "done":
                return
            if state == "visiting":
                return  # cycle - break it, order is best-effort
            visited[name] = "visiting"
            for dep in deps.get(name, []):
                visit(dep)
            visited[name] = "done"
            ordered.append(name)

        for model_name in models:
            visit(model_name)

        return ordered

    # -- association analysis -------------------------------------------

    def _reverse_associations(self, models: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
        """Map target model -> list of {field, source_model} referencing it."""
        reverse: Dict[str, List[Dict[str, str]]] = {}
        for model_name, model_config in models.items():
            for field_name, field_config in model_config.get("fields", {}).items():
                if field_config.get("type") == "foreign_key":
                    target = field_config.get("model")
                    if target:
                        reverse.setdefault(target, []).append(
                            {"field": field_name, "source_model": model_name}
                        )
        return reverse

    # -- file builders -----------------------------------------------------

    def _gemfile(self, context: Dict[str, Any]) -> str:
        return (
            "source 'https://rubygems.org'\n\n"
            "ruby '3.2.2'\n\n"
            "gem 'rails', '~> 7.1'\n"
            "gem 'pg', '~> 1.5'\n"
            "gem 'puma', '~> 6.4'\n"
            "gem 'bcrypt', '~> 3.1'\n"
            "gem 'rack-cors'\n"
            "gem 'jwt'\n\n"
            "group :development, :test do\n"
            "  gem 'rspec-rails'\n"
            "  gem 'factory_bot_rails'\n"
            "end\n"
        )

    def _database_yml(self, context: Dict[str, Any]) -> str:
        db_name = context["meta"]["name"].replace("-", "_")
        return (
            "default: &default\n"
            "  adapter: postgresql\n"
            "  encoding: unicode\n"
            '  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>\n'
            '  host: <%= ENV.fetch("DB_HOST") { "localhost" } %>\n'
            '  username: <%= ENV.fetch("DB_USER") { "postgres" } %>\n'
            '  password: <%= ENV.fetch("DB_PASSWORD") { "" } %>\n\n'
            "development:\n"
            "  <<: *default\n"
            f"  database: {db_name}_development\n\n"
            "test:\n"
            "  <<: *default\n"
            f"  database: {db_name}_test\n\n"
            "production:\n"
            "  <<: *default\n"
            f"  database: {db_name}_production\n"
            "  url: <%= ENV['DATABASE_URL'] %>\n"
        )

    def _application_controller(self) -> str:
        return (
            "class ApplicationController < ActionController::API\n"
            "  rescue_from ActiveRecord::RecordNotFound, with: :not_found\n\n"
            "  private\n\n"
            "  def not_found\n"
            "    render json: { error: 'not found' }, status: :not_found\n"
            "  end\n"
            "end\n"
        )

    def _model_rb(
        self,
        model_name: str,
        model_config: Dict[str, Any],
        context: Dict[str, Any],
        reverse_refs: List[Dict[str, str]],
    ) -> str:
        lines = [f"class {model_name} < ApplicationRecord"]
        fields = model_config.get("fields", {})

        for field_name, field_config in fields.items():
            if field_config.get("type") == "foreign_key":
                target = field_config.get("model", "")
                optional = "false" if field_config.get("required") else "true"
                lines.append(
                    f"  belongs_to :{field_name}, class_name: '{target}', optional: {optional}"
                )
            elif field_config.get("type") == "many_to_many":
                target = field_config.get("model", "")
                join_table = self._join_table(model_name, target)
                lines.append(
                    f"  has_and_belongs_to_many :{_plural(_snake(field_name))}, "
                    f"class_name: '{target}', join_table: :{join_table}"
                )

        for ref in reverse_refs:
            assoc_name = _plural(_snake(ref["source_model"]))
            lines.append(
                f"  has_many :{assoc_name}, class_name: '{ref['source_model']}', "
                f"foreign_key: '{ref['field']}_id', dependent: :destroy"
            )

        lines.append("")

        for field_name, field_config in fields.items():
            if field_config.get("primary_key"):
                continue
            validations = []
            if field_config.get("required"):
                validations.append("presence: true")
            if field_config.get("unique"):
                validations.append("uniqueness: true")
            if field_config.get("max_length") and field_config.get("type") == "string":
                validations.append(f"length: {{ maximum: {field_config['max_length']} }}")
            if field_config.get("type") == "choice" and field_config.get("choices"):
                choices = " ".join(field_config["choices"])
                validations.append(f"inclusion: {{ in: %w[{choices}] }}")
            if validations:
                lines.append(f"  validates :{field_name}, {', '.join(validations)}")

        hashed_fields = [name for name, cfg in fields.items() if cfg.get("hashed")]
        if hashed_fields:
            # `has_secure_password` requires a `<attr>_digest` column by
            # Rails convention, which the migration doesn't create (the
            # DSL names the column after the field itself, e.g. `password`)
            # so hash it in place with bcrypt on save instead.
            lines.append("")
            lines.append("  before_save do")
            for field_name in hashed_fields:
                lines.append(
                    f"    self.{field_name} = BCrypt::Password.create({field_name}) "
                    f"if {field_name}_changed? && {field_name}.present?"
                )
            lines.append("  end")

        lines.append("end")
        return "\n".join(lines) + "\n"

    def _join_table(self, model_name: str, field_name: str) -> str:
        names = sorted([_plural(_snake(model_name)), _plural(_snake(field_name))])
        return "_".join(names)

    def _permitted_params(self, fields: Dict[str, Any]) -> List[str]:
        """Build a Rails strong-params permit() list that matches the actual
        column/association names the migrations + models create - a plain
        `:author` would be silently stripped by Rails since the real column
        is `author_id` (and many_to_many needs `field_ids: []`, not `:field`).

        Bare-hash args like `tag_ids: []` are only valid Ruby syntax as the
        *trailing* arguments in a call, so scalar `:symbol` entries are
        collected first and the `key: []` entries are appended after.
        """
        scalar_parts: List[str] = []
        hash_parts: List[str] = []
        for field_name, field_config in fields.items():
            if field_config.get("auto_generated") or field_config.get("primary_key"):
                continue
            f_type = field_config.get("type")
            if f_type == "foreign_key":
                scalar_parts.append(f":{field_name}_id")
            elif f_type == "many_to_many":
                singular = field_name[:-1] if field_name.endswith("s") else field_name
                hash_parts.append(f"{singular}_ids: []")
            else:
                scalar_parts.append(f":{field_name}")
        return scalar_parts + hash_parts

    def _controller_rb(
        self, model_name: str, model_config: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        table = _plural(_snake(model_name))
        var = _snake(model_name)
        fields = model_config.get("fields", {})
        permitted_list = ", ".join(self._permitted_params(fields))

        return (
            "module Api\n"
            "  module V1\n"
            f"    class {_camelize(table)}Controller < ApplicationController\n"
            f"      before_action :set_{var}, only: [:show, :update, :destroy]\n\n"
            "      def index\n"
            f"        render json: {model_name}.all\n"
            "      end\n\n"
            "      def show\n"
            f"        render json: @{var}\n"
            "      end\n\n"
            "      def create\n"
            f"        {var} = {model_name}.new({var}_params)\n"
            f"        if {var}.save\n"
            f"          render json: {var}, status: :created\n"
            "        else\n"
            f"          render json: {{ errors: {var}.errors.full_messages }}, status: :unprocessable_entity\n"
            "        end\n"
            "      end\n\n"
            "      def update\n"
            f"        if @{var}.update({var}_params)\n"
            f"          render json: @{var}\n"
            "        else\n"
            f"          render json: {{ errors: @{var}.errors.full_messages }}, status: :unprocessable_entity\n"
            "        end\n"
            "      end\n\n"
            "      def destroy\n"
            f"        @{var}.destroy\n"
            "        head :no_content\n"
            "      end\n\n"
            "      private\n\n"
            f"      def set_{var}\n"
            f"        @{var} = {model_name}.find(params[:id])\n"
            "      end\n\n"
            f"      def {var}_params\n"
            f"        params.require(:{var}).permit({permitted_list})\n"
            "      end\n"
            "    end\n"
            "  end\n"
            "end\n"
        )

    def _migration_rb(self, model_name: str, model_config: Dict[str, Any]) -> str:
        table = _plural(_snake(model_name))
        class_name = f"Create{_camelize(table)}"
        fields = model_config.get("fields", {})

        lines = [
            f"class {class_name} < ActiveRecord::Migration[7.1]",
            "  def change",
            "    enable_extension 'pgcrypto' unless extension_enabled?('pgcrypto')",
            "",
            f"    create_table :{table}, id: :uuid, default: -> {{ \"gen_random_uuid()\" }} do |t|",
        ]

        for field_name, field_config in fields.items():
            if field_config.get("primary_key"):
                continue
            f_type = field_config.get("type", "string")
            if f_type == "foreign_key":
                lines.append(
                    f"      t.references :{field_name}, type: :uuid, "
                    f"foreign_key: {{ to_table: :{_plural(_snake(field_config.get('model', '')))} }}, "
                    f"null: {'false' if field_config.get('required') else 'true'}"
                )
                continue
            if f_type == "many_to_many":
                continue

            col_type = _MIGRATION_TYPES.get(f_type, "string")
            opts = []
            if field_config.get("required"):
                opts.append("null: false")
            if field_config.get("unique"):
                opts.append("index: { unique: true }")
            if col_type == "boolean" and "default" in field_config:
                opts.append(f"default: {str(bool(field_config['default'])).lower()}")
            if col_type == "string" and field_config.get("max_length"):
                opts.append(f"limit: {field_config['max_length']}")
            opts_str = f", {', '.join(opts)}" if opts else ""
            lines.append(f"      t.{col_type} :{field_name}{opts_str}")

        if not any(f.get("auto_now_add") or f.get("auto_now") for f in fields.values()):
            lines.append("      t.timestamps")

        lines.append("    end")
        lines.append("  end")
        lines.append("end")
        return "\n".join(lines) + "\n"

    def _join_migration_rb(self, join_table: str, left_table: str, right_table: str) -> str:
        class_name = f"Create{_camelize(join_table)}"
        left_singular = left_table[:-1] if left_table.endswith("s") else left_table
        right_singular = right_table[:-1] if right_table.endswith("s") else right_table
        return (
            f"class {class_name} < ActiveRecord::Migration[7.1]\n"
            "  def change\n"
            f"    create_join_table :{left_table}, :{right_table}, table_name: :{join_table} do |t|\n"
            f"      t.column :{left_singular}_id, :uuid\n"
            f"      t.column :{right_singular}_id, :uuid\n"
            f"      t.index [:{left_singular}_id, :{right_singular}_id], name: 'index_{join_table}_on_both_ids'\n"
            "    end\n"
            "  end\n"
            "end\n"
        )

    def _routes_rb(self, context: Dict[str, Any]) -> str:
        models = list(context.get("models", {}).keys())
        resource_lines = "\n".join(f"      resources :{_plural(_snake(m))}" for m in models)
        return (
            "Rails.application.routes.draw do\n"
            "  get '/health', to: proc { [200, {}, [{ status: 'healthy' }.to_json]] }\n\n"
            "  namespace :api do\n"
            "    namespace :v1 do\n"
            f"{resource_lines}\n"
            "    end\n"
            "  end\n"
            "end\n"
        )

    def _dockerfile(self, context: Dict[str, Any]) -> str:
        port = context["deployment"]["docker"].get("port", 3000)
        return (
            "FROM ruby:3.2-slim\n\n"
            "RUN apt-get update -qq && apt-get install -y build-essential libpq-dev curl "
            "&& rm -rf /var/lib/apt/lists/*\n\n"
            "WORKDIR /app\n"
            "COPY Gemfile ./\n"
            "RUN bundle install\n"
            "COPY . .\n\n"
            f"EXPOSE {port}\n"
            "HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f "
            f"http://localhost:{port}/health || exit 1\n\n"
            f'CMD ["rails", "server", "-b", "0.0.0.0", "-p", "{port}"]\n'
        )

    def _env_example(self, context: Dict[str, Any]) -> str:
        return (
            "RAILS_ENV=development\n"
            "RAILS_MAX_THREADS=5\n"
            "DB_HOST=localhost\n"
            "DB_USER=postgres\n"
            "DB_PASSWORD=\n"
            "DATABASE_URL=\n"
            "SECRET_KEY_BASE=change-me-in-production\n"
        )

    def _readme(self, context: Dict[str, Any]) -> str:
        meta = context["meta"]
        port = context["deployment"]["docker"].get("port", 3000)
        return (
            f"# {meta['name']} (Ruby on Rails API)\n\n"
            f"{meta.get('description', '')}\n\n"
            "Generated by InfraNest from a DSL specification.\n\n"
            "## Setup\n\n"
            "```bash\n"
            "cp .env.example .env\n"
            "bundle install\n"
            "bin/rails db:create db:migrate\n"
            f"bin/rails server -p {port}\n"
            "```\n\n"
            "## Docker\n\n"
            "```bash\n"
            f"docker build -t {meta['name']} .\n"
            f"docker run -p {port}:{port} --env-file .env {meta['name']}\n"
            "```\n"
        )
