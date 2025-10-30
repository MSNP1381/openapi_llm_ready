import json
import os
from pathlib import Path
from typing import Dict, Any, List, Set
import argparse


def load_openapi(path: str = "openapi.json") -> Dict[str, Any]:
    """Load OpenAPI specification from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_ref(ref_path: str, openapi_spec: Dict[str, Any]) -> Any:
    """
    Resolve a $ref pointer to its actual value in the OpenAPI spec.
    
    Args:
        ref_path: Reference path like "#/components/schemas/SchemaName"
        openapi_spec: The full OpenAPI specification
    
    Returns:
        The resolved object from the specification
    """
    if not ref_path.startswith("#/"):
        return None
    
    parts = ref_path[2:].split("/")
    current = openapi_spec
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current


def format_schema(schema: Any, openapi_spec: Dict[str, Any], indent: int = 0, seen_refs: Set[str] = None, inline_refs: bool = True) -> str:
    """
    Format a schema object as readable markdown with resolved references.
    
    Args:
        schema: The schema object to format
        openapi_spec: The full OpenAPI specification for resolving refs
        indent: Current indentation level
        seen_refs: Set of already seen references to avoid circular refs
        inline_refs: Whether to inline the full resolved schema (True) or just reference it (False)
    
    Returns:
        Formatted markdown string
    """
    if seen_refs is None:
        seen_refs = set()
    
    indent_str = "  " * indent
    
    if not isinstance(schema, dict):
        return f"{indent_str}- `{schema}`\n"
    
    # Handle $ref
    if "$ref" in schema:
        ref_path = schema["$ref"]
        
        # Always show the reference path first
        result = f"{indent_str}- **$ref**: `{ref_path}`\n"
        
        # Avoid circular references
        if ref_path in seen_refs:
            result += f"{indent_str}  *(circular reference, see definition above)*\n"
            return result
        
        seen_refs.add(ref_path)
        
        # Resolve and inline the referenced schema if inline_refs is True
        if inline_refs:
            resolved = resolve_ref(ref_path, openapi_spec)
            if resolved:
                result += f"{indent_str}  **Resolved Definition**:\n"
                result += format_schema(resolved, openapi_spec, indent + 1, seen_refs.copy(), inline_refs)
            else:
                result += f"{indent_str}  *(unable to resolve reference)*\n"
        
        return result
    
    result = ""
    
    # Handle type
    if "type" in schema:
        result += f"{indent_str}- **Type**: `{schema['type']}`\n"
    
    # Handle description
    if "description" in schema:
        result += f"{indent_str}- **Description**: {schema['description']}\n"
    
    # Handle title
    if "title" in schema:
        result += f"{indent_str}- **Title**: {schema['title']}\n"
    
    # Handle enum
    if "enum" in schema:
        result += f"{indent_str}- **Enum**: {', '.join(f'`{e}`' for e in schema['enum'])}\n"
    
    # Handle default
    if "default" in schema:
        result += f"{indent_str}- **Default**: `{schema['default']}`\n"
    
    # Handle format
    if "format" in schema:
        result += f"{indent_str}- **Format**: `{schema['format']}`\n"
    
    # Handle properties (for object type)
    if "properties" in schema:
        result += f"{indent_str}- **Properties**:\n"
        for prop_name, prop_schema in schema["properties"].items():
            required_marker = " *(required)*" if prop_name in schema.get("required", []) else ""
            result += f"{indent_str}  - **`{prop_name}`**{required_marker}:\n"
            result += format_schema(prop_schema, openapi_spec, indent + 2, seen_refs.copy(), inline_refs)
    
    # Handle items (for array type)
    if "items" in schema:
        result += f"{indent_str}- **Items**:\n"
        result += format_schema(schema["items"], openapi_spec, indent + 1, seen_refs.copy(), inline_refs)
    
    # Handle allOf, anyOf, oneOf
    for key in ["allOf", "anyOf", "oneOf"]:
        if key in schema:
            result += f"{indent_str}- **{key}**:\n"
            for i, sub_schema in enumerate(schema[key]):
                result += f"{indent_str}  - Option {i + 1}:\n"
                result += format_schema(sub_schema, openapi_spec, indent + 2, seen_refs.copy(), inline_refs)
    
    # Handle additional properties
    if "additionalProperties" in schema and schema["additionalProperties"] not in [True, False]:
        result += f"{indent_str}- **Additional Properties**:\n"
        result += format_schema(schema["additionalProperties"], openapi_spec, indent + 1, seen_refs.copy(), inline_refs)
    
    # Handle required fields
    if "required" in schema and schema.get("type") != "object":
        result += f"{indent_str}- **Required**: {', '.join(f'`{r}`' for r in schema['required'])}\n"
    
    # Handle examples
    if "example" in schema:
        result += f"{indent_str}- **Example**: `{schema['example']}`\n"
    
    # Handle pattern
    if "pattern" in schema:
        result += f"{indent_str}- **Pattern**: `{schema['pattern']}`\n"
    
    # Handle min/max constraints
    for constraint in ["minimum", "maximum", "minLength", "maxLength", "minItems", "maxItems"]:
        if constraint in schema:
            result += f"{indent_str}- **{constraint}**: `{schema[constraint]}`\n"
    
    return result


def format_parameters(parameters: List[Dict], openapi_spec: Dict[str, Any], inline_refs: bool = True) -> str:
    """Format parameters section."""
    if not parameters:
        return "*No parameters*\n\n"
    
    result = ""
    for param in parameters:
        param_name = param.get("name", "unknown")
        param_in = param.get("in", "unknown")
        required = "**Required**" if param.get("required", False) else "Optional"
        description = param.get("description", "")
        
        result += f"- **`{param_name}`** ({param_in}) - {required}\n"
        if description:
            result += f"  - Description: {description}\n"
        
        if "schema" in param:
            result += "  - Schema:\n"
            result += format_schema(param["schema"], openapi_spec, indent=2, inline_refs=inline_refs)
        
        result += "\n"
    
    return result


def format_request_body(request_body: Dict, openapi_spec: Dict[str, Any], inline_refs: bool = True) -> str:
    """Format request body section."""
    if not request_body:
        return "*No request body*\n\n"
    
    result = ""
    required = request_body.get("required", False)
    result += f"**Required**: {required}\n\n"
    
    if "description" in request_body:
        result += f"**Description**: {request_body['description']}\n\n"
    
    if "content" in request_body:
        result += "**Content Types**:\n\n"
        for content_type, content_spec in request_body["content"].items():
            result += f"- **`{content_type}`**:\n"
            if "schema" in content_spec:
                result += format_schema(content_spec["schema"], openapi_spec, indent=1, inline_refs=inline_refs)
            result += "\n"
    
    return result


def format_responses(responses: Dict, openapi_spec: Dict[str, Any], inline_refs: bool = True) -> str:
    """Format responses section."""
    if not responses:
        return "*No responses defined*\n\n"
    
    result = ""
    for status_code, response_spec in responses.items():
        result += f"### Response: `{status_code}`\n\n"
        
        if "description" in response_spec:
            result += f"**Description**: {response_spec['description']}\n\n"
        
        if "content" in response_spec:
            result += "**Content**:\n\n"
            for content_type, content_spec in response_spec["content"].items():
                result += f"- **`{content_type}`**:\n"
                if "schema" in content_spec:
                    result += format_schema(content_spec["schema"], openapi_spec, indent=1, inline_refs=inline_refs)
                result += "\n"
        
        result += "---\n\n"
    
    return result


def format_endpoint(path: str, method: str, endpoint_data: Dict, openapi_spec: Dict[str, Any], inline_refs: bool = True) -> str:
    """
    Format a single endpoint as markdown documentation.
    
    Args:
        path: The API path (e.g., "/v1/products/{id}")
        method: HTTP method (e.g., "get", "post")
        endpoint_data: The endpoint specification
        openapi_spec: The full OpenAPI specification
        inline_refs: Whether to inline resolved $ref values
    
    Returns:
        Formatted markdown string for the endpoint
    """
    markdown = f"## `{method.upper()} {path}`\n\n"
    
    # Summary and description
    if "summary" in endpoint_data:
        markdown += f"**Summary**: {endpoint_data['summary']}\n\n"
    
    if "description" in endpoint_data:
        markdown += f"**Description**: {endpoint_data['description']}\n\n"
    
    if "operationId" in endpoint_data:
        markdown += f"**Operation ID**: `{endpoint_data['operationId']}`\n\n"
    
    # Tags
    if "tags" in endpoint_data:
        markdown += f"**Tags**: {', '.join(f'`{tag}`' for tag in endpoint_data['tags'])}\n\n"
    
    markdown += "---\n\n"
    
    # Parameters
    if "parameters" in endpoint_data and endpoint_data["parameters"]:
        markdown += "### Parameters\n\n"
        markdown += format_parameters(endpoint_data["parameters"], openapi_spec, inline_refs=inline_refs)
    
    # Request Body
    if "requestBody" in endpoint_data:
        markdown += "### Request Body\n\n"
        markdown += format_request_body(endpoint_data["requestBody"], openapi_spec, inline_refs=inline_refs)
    
    # Responses
    if "responses" in endpoint_data:
        markdown += "### Responses\n\n"
        markdown += format_responses(endpoint_data["responses"], openapi_spec, inline_refs=inline_refs)
    
    # Security
    if "security" in endpoint_data:
        markdown += "### Security\n\n"
        for security_req in endpoint_data["security"]:
            for scheme_name, scopes in security_req.items():
                markdown += f"- **{scheme_name}**: {scopes if scopes else 'No scopes required'}\n"
        markdown += "\n"
    
    markdown += "\n---\n\n"
    
    return markdown


def generate_category_docs(openapi_spec: Dict[str, Any], output_dir: str = "docs", 
                          chunk_by_category: bool = True, inline_refs: bool = True) -> None:
    """
    Generate markdown documentation files from OpenAPI specification.
    
    Args:
        openapi_spec: The OpenAPI specification
        output_dir: Directory to write markdown files to
        chunk_by_category: If True, create separate files per category/tag. 
                          If False, create a single comprehensive file.
        inline_refs: If True, resolve and inline $ref values in the documentation
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Extract all endpoints grouped by category
    categories: Dict[str, List[tuple]] = {}
    
    for path, path_data in openapi_spec.get("paths", {}).items():
        for method, endpoint_data in path_data.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                continue
            
            tags = endpoint_data.get("tags", ["Uncategorized"])
            
            for tag in tags:
                if tag not in categories:
                    categories[tag] = []
                categories[tag].append((path, method, endpoint_data))
    
    if chunk_by_category:
        # Generate a markdown file for each category
        for category, endpoints in sorted(categories.items()):
            filename = f"{category.lower().replace(' ', '_')}.md"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Header
                f.write(f"# {category} API Documentation\n\n")
                f.write(f"This document contains all endpoints tagged with `{category}`.\n\n")
                
                # Info section
                if "info" in openapi_spec:
                    info = openapi_spec["info"]
                    f.write(f"**API Title**: {info.get('title', 'N/A')}\n\n")
                    f.write(f"**API Version**: {info.get('version', 'N/A')}\n\n")
                    if "description" in info:
                        f.write(f"**Description**: {info['description']}\n\n")
                
                # Server information
                if "servers" in openapi_spec and openapi_spec["servers"]:
                    f.write("**Base URLs**:\n\n")
                    for server in openapi_spec["servers"]:
                        url = server.get("url", "N/A")
                        description = server.get("description", "")
                        f.write(f"- `{url}`")
                        if description:
                            f.write(f" - {description}")
                        f.write("\n")
                    f.write("\n")
                
                f.write("---\n\n")
                
                # Table of contents
                f.write("## Table of Contents\n\n")
                for i, (path, method, endpoint_data) in enumerate(endpoints, 1):
                    summary = endpoint_data.get("summary", path)
                    anchor = f"{method.lower()}-{path.replace('/', '').replace('{', '').replace('}', '').replace('_', '-')}"
                    f.write(f"{i}. [{method.upper()} {path}](#{anchor}): {summary}\n")
                f.write("\n---\n\n")
                
                # Endpoints
                for path, method, endpoint_data in endpoints:
                    endpoint_md = format_endpoint(path, method, endpoint_data, openapi_spec, inline_refs=inline_refs)
                    f.write(endpoint_md)
            
            print(f"✓ Generated {filepath} with {len(endpoints)} endpoints")
        
        # Generate an index file
        index_path = output_path / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# API Documentation Index\n\n")
            
            if "info" in openapi_spec:
                info = openapi_spec["info"]
                f.write(f"## {info.get('title', 'API Documentation')}\n\n")
                f.write(f"**Version**: {info.get('version', 'N/A')}\n\n")
                if "description" in info:
                    f.write(f"{info['description']}\n\n")
            
            # Server information
            if "servers" in openapi_spec and openapi_spec["servers"]:
                f.write("**Base URLs**:\n\n")
                for server in openapi_spec["servers"]:
                    url = server.get("url", "N/A")
                    description = server.get("description", "")
                    f.write(f"- `{url}`")
                    if description:
                        f.write(f" - {description}")
                    f.write("\n")
                f.write("\n")
            
            f.write("## Categories\n\n")
            for category in sorted(categories.keys()):
                endpoint_count = len(categories[category])
                filename = f"{category.lower().replace(' ', '_')}.md"
                f.write(f"- [{category}]({filename}) - {endpoint_count} endpoint{'s' if endpoint_count != 1 else ''}\n")
            
            f.write("\n---\n\n")
            f.write(f"*Generated from OpenAPI specification*\n")
        
        print(f"✓ Generated index at {index_path}")
    
    else:
        # Generate a single comprehensive file
        filepath = output_path / "api_documentation.md"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write("# Complete API Documentation\n\n")
            
            # Info section
            if "info" in openapi_spec:
                info = openapi_spec["info"]
                f.write(f"## {info.get('title', 'API Documentation')}\n\n")
                f.write(f"**Version**: {info.get('version', 'N/A')}\n\n")
                if "description" in info:
                    f.write(f"{info['description']}\n\n")
            
            # Server information
            if "servers" in openapi_spec and openapi_spec["servers"]:
                f.write("**Base URLs**:\n\n")
                for server in openapi_spec["servers"]:
                    url = server.get("url", "N/A")
                    description = server.get("description", "")
                    f.write(f"- `{url}`")
                    if description:
                        f.write(f" - {description}")
                    f.write("\n")
                f.write("\n")
            
            f.write("---\n\n")
            
            # Generate table of contents by category
            f.write("## Table of Contents\n\n")
            for category in sorted(categories.keys()):
                f.write(f"### {category}\n\n")
                for path, method, endpoint_data in categories[category]:
                    summary = endpoint_data.get("summary", path)
                    anchor = f"{method.lower()}-{path.replace('/', '').replace('{', '').replace('}', '').replace('_', '-')}"
                    f.write(f"- [{method.upper()} {path}](#{anchor}): {summary}\n")
                f.write("\n")
            
            f.write("---\n\n")
            
            # Generate all endpoints organized by category
            for category in sorted(categories.keys()):
                f.write(f"# {category}\n\n")
                
                for path, method, endpoint_data in categories[category]:
                    endpoint_md = format_endpoint(path, method, endpoint_data, openapi_spec, inline_refs=inline_refs)
                    f.write(endpoint_md)
        
        print(f"✓ Generated single documentation file at {filepath}")
        total_endpoints = sum(len(endpoints) for endpoints in categories.values())
        print(f"   Total endpoints: {total_endpoints} across {len(categories)} categories")


def main():
    """Main function to generate LLM-ready documentation from OpenAPI spec."""
    parser = argparse.ArgumentParser(
        description='Generate LLM-ready markdown documentation from OpenAPI specification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate category-based documentation with inlined references (default)
  python main.py
  
  # Generate a single comprehensive file
  python main.py --no-chunk-by-category
  
  # Only show $ref paths without inlining resolved schemas
  python main.py --no-inline-refs
  
  # Combine options
  python main.py --no-chunk-by-category --no-inline-refs
  
  # Specify custom input/output paths
  python main.py -i my_api.json -o output_docs/
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        default='openapi.json',
        help='Path to OpenAPI JSON file (default: openapi.json)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='docs',
        help='Output directory for markdown files (default: docs/)'
    )
    
    parser.add_argument(
        '--no-chunk-by-category',
        action='store_true',
        help='Generate a single comprehensive file instead of separate files per category'
    )
    
    parser.add_argument(
        '--no-inline-refs',
        action='store_true',
        help='Do not inline resolved $ref schemas (only show reference paths)'
    )
    
    args = parser.parse_args()
    
    # Derive settings from arguments
    chunk_by_category = not args.no_chunk_by_category
    inline_refs = not args.no_inline_refs
    
    print(f"Loading OpenAPI specification from: {args.input}")
    try:
        openapi_spec = load_openapi(args.input)
    except FileNotFoundError:
        print(f"❌ Error: File '{args.input}' not found")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{args.input}': {e}")
        return
    
    print(f"Generating documentation...")
    print(f"  - Chunking by category: {'Yes' if chunk_by_category else 'No'}")
    print(f"  - Inlining $ref values: {'Yes' if inline_refs else 'No'}")
    print(f"  - Output directory: {args.output}")
    print()
    
    generate_category_docs(
        openapi_spec, 
        output_dir=args.output, 
        chunk_by_category=chunk_by_category,
        inline_refs=inline_refs
    )
    
    print("\n✅ Documentation generation complete!")
    print(f"   Files written to: {args.output}/")


if __name__ == "__main__":
    main()