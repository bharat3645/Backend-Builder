"""
Backend Builder code generators.

Each generator turns a validated DSL specification (as produced by
``parsers.dsl_parser.DSLParser``) into a dictionary mapping relative file
paths to file contents for a specific backend framework.
"""

from .django_generator import DjangoGenerator
from .go_generator import GoGenerator
from .rails_generator import RailsGenerator

__all__ = ["DjangoGenerator", "GoGenerator", "RailsGenerator"]
