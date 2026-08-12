"""
DSL Parser for Backend Builder
Validates and parses DSL specifications into structured data
"""

import yaml
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class DSLParser:
    """Parser for Backend Builder DSL specifications"""
    
    def __init__(self):
        self.required_sections = ['meta', 'models']
        self.optional_sections = ['auth', 'api', 'jobs', 'deployment']
        self.field_types = [
            'string', 'text', 'integer', 'float', 'boolean', 'datetime', 
            'date', 'uuid', 'url', 'email', 'json', 'foreign_key', 
            'many_to_many', 'choice'
        ]
        
    def parse(self, dsl_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate DSL specification"""
        # Guard against YAML foot-guns like an unquoted `null:` key, which
        # PyYAML parses as the Python `None` key rather than the string
        # "null" - that silently breaks field lookups (e.g. `null: true`
        # meant as `null=True`) and crashes JSON serialization of any
        # response that echoes the spec back.
        dsl_spec = self._sanitize_keys(dsl_spec)

        validation_result = self.validate(dsl_spec)
        
        if not validation_result['valid']:
            raise ValueError(f"Invalid DSL specification: {validation_result['errors']}")
        
        # Normalize and enrich the specification
        normalized_spec = self._normalize_spec(dsl_spec)
        
        return normalized_spec
    
    def _sanitize_keys(self, value: Any) -> Any:
        """Recursively coerce non-string dict keys (None, bool, int) to str."""
        if isinstance(value, dict):
            return {
                (k if isinstance(k, str) else json.dumps(k) if isinstance(k, (bool, type(None))) else str(k)): self._sanitize_keys(v)
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [self._sanitize_keys(item) for item in value]
        return value

    def validate(self, dsl_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DSL specification"""
        errors = []
        warnings = []
        
        # Check required sections
        for section in self.required_sections:
            if section not in dsl_spec:
                errors.append(f"Missing required section: {section}")
        
        # Validate meta section
        if 'meta' in dsl_spec:
            meta_errors = self._validate_meta(dsl_spec['meta'])
            errors.extend(meta_errors)
        
        # Validate models section
        if 'models' in dsl_spec:
            model_errors, model_warnings = self._validate_models(dsl_spec['models'])
            errors.extend(model_errors)
            warnings.extend(model_warnings)
        
        # Validate auth section
        if 'auth' in dsl_spec:
            auth_errors = self._validate_auth(dsl_spec['auth'])
            errors.extend(auth_errors)
        
        # Validate API section
        if 'api' in dsl_spec:
            api_errors = self._validate_api(dsl_spec['api'])
            errors.extend(api_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_meta(self, meta: Dict[str, Any]) -> List[str]:
        """Validate meta section"""
        errors = []
        required_fields = ['name', 'version', 'framework']
        
        for field in required_fields:
            if field not in meta:
                errors.append(f"Missing required field in meta: {field}")
        
        # Validate framework
        if 'framework' in meta:
            supported_frameworks = ['django', 'go-fiber', 'rails']
            if meta['framework'] not in supported_frameworks:
                errors.append(f"Unsupported framework: {meta['framework']}. Supported: {supported_frameworks}")
        
        # Validate name format
        if 'name' in meta:
            if not re.match(r'^[a-z0-9-_]+$', meta['name']):
                errors.append("Project name must contain only lowercase letters, numbers, hyphens, and underscores")
        
        return errors
    
    def _validate_models(self, models: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Validate models section"""
        errors = []
        warnings = []
        
        for model_name, model_def in models.items():
            # Validate model name
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', model_name):
                errors.append(f"Model name '{model_name}' must start with uppercase letter and contain only letters and numbers")
            
            # Validate fields
            if 'fields' not in model_def:
                errors.append(f"Model '{model_name}' must have a 'fields' section")
                continue
            
            primary_key_count = 0
            for field_name, field_def in model_def['fields'].items():
                # Validate field type
                if 'type' not in field_def:
                    errors.append(f"Field '{field_name}' in model '{model_name}' must have a 'type'")
                    continue
                
                if field_def['type'] not in self.field_types:
                    errors.append(f"Invalid field type '{field_def['type']}' for field '{field_name}' in model '{model_name}'")
                
                # Count primary keys
                if field_def.get('primary_key', False):
                    primary_key_count += 1
            
            # Validate primary key
            if primary_key_count == 0:
                warnings.append(f"Model '{model_name}' has no primary key. An 'id' field will be auto-generated.")
            elif primary_key_count > 1:
                errors.append(f"Model '{model_name}' has multiple primary keys")
        
        return errors, warnings
    
    def _validate_auth(self, auth: Dict[str, Any]) -> List[str]:
        """Validate auth section"""
        errors = []

        if 'provider' not in auth:
            errors.append("Auth section must specify a 'provider'")
            return errors

        supported_providers = ['jwt', 'oauth2', 'custom']
        if auth.get('provider') not in supported_providers:
            errors.append(f"Unsupported auth provider: {auth.get('provider')}. Supported: {supported_providers}")

        return errors
    
    def _validate_api(self, api: Dict[str, Any]) -> List[str]:
        """Validate API section"""
        errors = []
        
        if 'endpoints' in api:
            for endpoint in api['endpoints']:
                if 'path' not in endpoint:
                    errors.append("API endpoint must have a 'path'")
                if 'method' not in endpoint:
                    errors.append("API endpoint must have a 'method'")
                if 'handler' not in endpoint:
                    errors.append("API endpoint must have a 'handler'")
        
        return errors
    
    def _normalize_spec(self, dsl_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and enrich DSL specification"""
        normalized = dsl_spec.copy()
        
        # Add default values
        if 'meta' not in normalized:
            normalized['meta'] = {}
        
        # Ensure all models have primary keys
        for model_name, model_def in normalized.get('models', {}).items():
            if 'fields' in model_def:
                has_primary_key = any(
                    field.get('primary_key', False) 
                    for field in model_def['fields'].values()
                )
                
                if not has_primary_key:
                    # Add auto-generated ID field
                    if 'id' not in model_def['fields']:
                        model_def['fields']['id'] = {
                            'type': 'uuid',
                            'primary_key': True,
                            'auto_generated': True
                        }
        
        return normalized