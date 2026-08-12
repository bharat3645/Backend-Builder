#!/usr/bin/env python3
"""
Generate a real project from a DSL file using Backend Builder's generators
directly (no running Flask server required).

Used by CI (.github/workflows/ci.yml) to produce output that the Django,
Go, and Rails toolchains can then actually build/check - the same kind of
verification described in the project's README - and is handy locally too:

    python core/scripts/generate_sample_projects.py \\
        --dsl dsl/example_blog.yml --framework go-fiber --out /tmp/out
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml  # noqa: E402

from generators.django_generator import DjangoGenerator  # noqa: E402
from generators.go_generator import GoGenerator  # noqa: E402
from generators.rails_generator import RailsGenerator  # noqa: E402
from parsers.dsl_parser import DSLParser  # noqa: E402

GENERATORS = {
    "django": DjangoGenerator,
    "go-fiber": GoGenerator,
    "rails": RailsGenerator,
}


def generate(dsl_path: str, framework: str, out_dir: str) -> int:
    with open(dsl_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    spec.setdefault("meta", {})["framework"] = framework

    parsed = DSLParser().parse(spec)
    files = GENERATORS[framework]().generate(parsed)

    for rel_path, content in files.items():
        full_path = os.path.join(out_dir, rel_path)
        os.makedirs(os.path.dirname(full_path) or out_dir, exist_ok=True)
        with open(full_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    print(f"[{framework}] wrote {len(files)} files to {out_dir}")
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsl", required=True, help="Path to a DSL YAML file")
    parser.add_argument(
        "--framework",
        required=True,
        choices=[*GENERATORS.keys(), "all"],
        help="Target framework, or 'all' to generate every framework into <out>/<framework>/",
    )
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    if args.framework == "all":
        for framework in GENERATORS:
            generate(args.dsl, framework, os.path.join(args.out, framework))
    else:
        generate(args.dsl, args.framework, args.out)


if __name__ == "__main__":
    main()
