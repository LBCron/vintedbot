#!/usr/bin/env python3
"""
OpenAPI Client Generator for Lovable.dev Frontend

This script downloads the OpenAPI specification from the running backend
and generates TypeScript types that can be imported into Lovable.

Usage:
    python frontend/openapi_client/generate_client.py
    
The generated files will be placed in frontend/openapi_client/
"""

import json
import requests
from pathlib import Path


def fetch_openapi_spec(base_url: str = "http://localhost:5000") -> dict:
    """Fetch OpenAPI specification from the backend"""
    print(f"🔍 Fetching OpenAPI spec from {base_url}/openapi.json...")
    response = requests.get(f"{base_url}/openapi.json")
    response.raise_for_status()
    return response.json()


def generate_typescript_types(spec: dict) -> str:
    """Generate TypeScript types from OpenAPI schemas"""
    schemas = spec.get("components", {}).get("schemas", {})
    
    ts_code = """// Auto-generated TypeScript types from VintedBot API
// Generated from OpenAPI specification
// DO NOT EDIT - This file is auto-generated

"""
    
    for schema_name, schema_def in schemas.items():
        if schema_def.get("type") == "object":
            ts_code += f"\nexport interface {schema_name} {{\n"
            properties = schema_def.get("properties", {})
            required = schema_def.get("required", [])
            
            for prop_name, prop_def in properties.items():
                is_required = prop_name in required
                optional = "" if is_required else "?"
                
                ts_type = python_type_to_ts(prop_def)
                ts_code += f"  {prop_name}{optional}: {ts_type};\n"
            
            ts_code += "}\n"
        
        elif schema_def.get("enum"):
            enum_values = schema_def["enum"]
            ts_code += f"\nexport type {schema_name} = "
            ts_code += " | ".join([f'"{val}"' for val in enum_values])
            ts_code += ";\n"
    
    return ts_code


def python_type_to_ts(prop_def: dict, depth: int = 0) -> str:
    """Convert Python/OpenAPI type to TypeScript type"""
    if depth > 5:
        return "any"
    
    if "anyOf" in prop_def:
        types = [python_type_to_ts(t, depth + 1) for t in prop_def["anyOf"]]
        return " | ".join(types)
    
    if "allOf" in prop_def:
        return "any"
    
    if "$ref" in prop_def:
        return prop_def["$ref"].split("/")[-1]
    
    prop_type = prop_def.get("type", "any")
    
    if prop_type == "array":
        item_type = prop_def.get("items", {})
        if "$ref" in item_type:
            ref_type = item_type["$ref"].split("/")[-1]
            return f"{ref_type}[]"
        else:
            item_ts = python_type_to_ts(item_type, depth + 1)
            return f"Array<{item_ts}>"
    
    type_map = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "object": "Record<string, any>",
    }
    
    return type_map.get(prop_type, "any")


def generate_api_client(spec: dict) -> str:
    """Generate TypeScript API client with all endpoints"""
    paths = spec.get("paths", {})
    
    client_code = """// Auto-generated API Client for VintedBot
// Generated from OpenAPI specification

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

class VintedBotAPI {
"""
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue
            
            operation_id = details.get("operationId", "")
            summary = details.get("summary", "")
            
            func_name = operation_id or path.replace("/", "_").replace("{", "").replace("}", "").strip("_")
            
            params = []
            path_params = []
            for param in details.get("parameters", []):
                param_name = param["name"]
                if param["in"] == "path":
                    path_params.append(param_name)
                    params.append(f"{param_name}: string")
            
            request_body = details.get("requestBody", {})
            if request_body:
                params.append("data: any")
            
            params_str = ", ".join(params) if params else ""
            
            client_code += f"\n  /**\n   * {summary}\n   */\n"
            client_code += f"  async {func_name}({params_str}) {{\n"
            
            url_path = path
            for param in path_params:
                url_path = url_path.replace(f"{{{param}}}", f"${{{param}}}")
            
            client_code += f"    const response = await fetch(`${{API_BASE}}{url_path}`, {{\n"
            client_code += f"      method: '{method.upper()}',\n"
            
            if method.lower() in ["post", "put", "patch"]:
                client_code += f"      headers: {{\n"
                client_code += f"        'Content-Type': 'application/json',\n"
                client_code += f"      }},\n"
                if request_body:
                    client_code += f"      body: JSON.stringify(data),\n"
            
            client_code += f"    }});\n"
            
            responses = details.get("responses", {}).get("200", {})
            content_type = list(responses.get("content", {}).keys())[0] if responses.get("content") else "application/json"
            
            if "text/csv" in content_type or "text/plain" in content_type:
                client_code += f"    return response.text();\n"
            elif "application/pdf" in content_type or "application/octet-stream" in content_type:
                client_code += f"    return response.blob();\n"
            else:
                client_code += f"    const contentType = response.headers.get('content-type');\n"
                client_code += f"    if (contentType?.includes('application/json')) {{\n"
                client_code += f"      return response.json();\n"
                client_code += f"    }} else if (contentType?.includes('text/')) {{\n"
                client_code += f"      return response.text();\n"
                client_code += f"    }} else {{\n"
                client_code += f"      return response.blob();\n"
                client_code += f"    }}\n"
            client_code += f"  }}\n"
    
    client_code += "}\n\nexport const api = new VintedBotAPI();\n"
    
    return client_code


def main():
    """Main function to generate OpenAPI client"""
    try:
        spec = fetch_openapi_spec()
        
        output_dir = Path("frontend/openapi_client")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        types_file = output_dir / "types.ts"
        print(f"📝 Generating TypeScript types...")
        types_code = generate_typescript_types(spec)
        types_file.write_text(types_code)
        print(f"✅ Types written to {types_file}")
        
        client_file = output_dir / "client.ts"
        print(f"📝 Generating API client...")
        client_code = generate_api_client(spec)
        client_file.write_text(client_code)
        print(f"✅ Client written to {client_file}")
        
        spec_file = output_dir / "openapi.json"
        spec_file.write_text(json.dumps(spec, indent=2))
        print(f"✅ OpenAPI spec saved to {spec_file}")
        
        readme_file = output_dir / "README.md"
        readme_content = """# OpenAPI Client for Lovable.dev

## Auto-Generated Files

- `types.ts` - TypeScript interfaces and types
- `client.ts` - API client with all endpoints
- `openapi.json` - Full OpenAPI specification

## Usage in Lovable

Import the types and client in your Lovable frontend:

```typescript
import { api } from './openapi_client/client';
import { Item, Draft, Stats } from './openapi_client/types';

// Use the API client
const stats = await api.get_stats();
const listings = await api.get_all_listings();
const draft = await api.ingest_photos({ urls: ['https://example.com/photo.jpg'] });
```

## Regenerate

To regenerate after API changes:

```bash
python frontend/openapi_client/generate_client.py
```
"""
        readme_file.write_text(readme_content)
        print(f"✅ README written to {readme_file}")
        
        print("\n" + "="*60)
        print("✅ OpenAPI client generation complete!")
        print("="*60)
        print(f"\nGenerated files:")
        print(f"  - {types_file}")
        print(f"  - {client_file}")
        print(f"  - {spec_file}")
        print(f"  - {readme_file}")
        print("\nCopy the frontend/openapi_client/ folder to your Lovable project!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
