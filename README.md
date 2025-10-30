# OpenAPI to LLM-Ready Documentation Converter

A Python tool that converts OpenAPI specifications into comprehensive, LLM-ready markdown documentation with fully resolved schema references, plus a semantic search system for intelligent API discovery.

## Features

✨ **Complete Reference Resolution**: Automatically resolves and inlines all `$ref` values, showing both the reference path and the complete schema definition

📚 **Flexible Output Modes**:

- **Category-based chunking**: Generates separate markdown files for each API category/tag (default)
- **Single file mode**: Creates one comprehensive documentation file with all endpoints

🎯 **LLM-Optimized Format**:

- Clear, hierarchical markdown structure
- Complete schema information with all properties, types, and constraints
- Detailed parameter, request body, and response documentation
- Handles complex schemas (anyOf, allOf, oneOf, nested objects, arrays)

🔄 **Circular Reference Handling**: Detects and handles circular schema references gracefully

🔍 **Semantic Search**: ChromaDB + Gemini embeddings for intelligent API endpoint discovery

- Natural language queries
- Category and method filtering
- Path-based search
- Integration-ready for RAG systems

## Installation

```bash
# Install dependencies using uv (recommended)
uv sync

```

## Quick Start

### 1. Generate Documentation

```bash
# Generate category-based documentation (default)
python main.py

# This will:
# - Read from openapi.json
# - Generate separate .md files for each category
# - Create an index.md with overview
# - Output to docs/ directory
```

## Usage

### Basic Usage

```bash
# Generate category-based documentation (default)
python main.py

# This will:
# - Read from openapi.json
# - Generate separate .md files for each category
# - Create an index.md with overview
# - Output to docs/ directory
```

### Command-Line Options

```bash
# Show help
python main.py --help

# Specify custom input/output paths
python main.py -i my_api.json -o output_docs/

# Generate a single comprehensive file
python main.py --no-chunk-by-category

# Only show $ref paths without inlining schemas
python main.py --no-inline-refs

# Combine options
python main.py --no-chunk-by-category --no-inline-refs -o single_file_docs/
```

### Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--input` | `-i` | Path to OpenAPI JSON file | `openapi.json` |
| `--output` | `-o` | Output directory for markdown files | `docs/` |
| `--no-chunk-by-category` | - | Generate single file instead of per-category files | `False` (chunking enabled) |
| `--no-inline-refs` | - | Don't inline resolved schemas, only show `$ref` paths | `False` (inlining enabled) |

## Output Examples

### With Inlined References (Default)

When `inline_refs=True`, the tool shows both the reference path AND the complete resolved schema:

```markdown
### Request Body

**Content Types**:

- **`application/json`**:
  - **$ref**: `#/components/schemas/UpdateShelveSchema`
    **Resolved Definition**:
    - **Type**: `object`
    - **Title**: UpdateShelveSchema
    - **Properties**:
      - **`title`** *(required)*:
        - **Type**: `string`
        - **Title**: Title
      - **`description`**:
        - **Title**: Description
        - **anyOf**:
          - Option 1:
            - **Type**: `string`
          - Option 2:
            - **Type**: `null`
```

### Without Inlined References

When `--no-inline-refs` is used, only the reference path is shown:

```markdown
### Request Body

**Content Types**:

- **`application/json`**:
  - **$ref**: `#/components/schemas/UpdateShelveSchema`
```

### Category-Based Output (Default)

Creates multiple files:

- `docs/index.md` - Overview with links to all categories
- `docs/banking.md` - All Banking endpoints
- `docs/product.md` - All Product endpoints
- `docs/order.md` - All Order endpoints
- etc.

### Single File Output

Creates one comprehensive file:

- `docs/api_documentation.md` - All endpoints organized by category

## Schema Resolution Features

The tool handles complex OpenAPI schema features:

- ✅ `$ref` resolution with inline expansion
- ✅ Circular reference detection
- ✅ `allOf`, `anyOf`, `oneOf` compositions
- ✅ Nested objects and arrays
- ✅ Required field indicators
- ✅ Enum values
- ✅ Type constraints (min/max, pattern, format)
- ✅ Examples and defaults
- ✅ Multiple content types

## Project Structure

```text
.
├── main.py              # Main converter script
├── openapi.json         # Your OpenAPI specification
├── README.md            # This file
└── docs/                # Generated documentation (default output)
    ├── index.md         # Index file
    ├── category1.md     # Per-category files
    └── category2.md
```

## Use Cases

### For LLM Context

Perfect for providing API documentation to language models:

```bash
# Generate comprehensive single file for LLM context
python main.py --no-chunk-by-category -o llm_context/

# The resulting file contains all endpoints with fully resolved schemas
# Ideal for RAG systems or direct LLM context
```

### For Human Documentation

```bash
# Generate readable, organized documentation
python main.py

# Creates easy-to-navigate category-based docs
# Perfect for developer portals or documentation sites
```

### For API Exploration

```bash
# Quick reference without schema details
python main.py --no-inline-refs -o quick_ref/

# Generates lighter files showing API structure
# Good for getting an overview of the API
```

## Example Output Statistics

For a typical OpenAPI spec with 95 endpoints across 15 categories:

- **Category-based mode**: Generates 16 files (15 category files + 1 index)
- **Single file mode**: Generates 1 comprehensive file (~39,000 lines with full resolution)
- **Processing time**: < 5 seconds for large specs




## Project Structure

```text
.
├── main.py                  # Documentation generator
├── openapi.json            # Your OpenAPI specification
├── README.md               # This file
├── pyproject.toml          # Project dependencies
├── docs/                   # Generated documentation
    ├── index.md           # Index file
    ├── category1.md       # Per-category files
    └── category2.md
```

## License

This is a utility script for converting OpenAPI specifications to markdown documentation.

## Contributing

Feel free to open issues or submit pull requests for improvements!

Generate LLM-ready Markdown documentation from an OpenAPI 3.x JSON file.

## Features

- Walks every endpoint/method and produces readable sections (parameters, body, responses).
- Links each referenced component schema with stable anchors for easy cross-referencing.
- Includes a component appendix with property details and enum values.

## Requirements

- Python 3.12 or newer (standard library only).
- An OpenAPI document in JSON format (default: `openapi.json` in the project directory).

## Usage

```bash
python3 main.py --input openapi.json --output openapi.md
```

CLI options:

- `--input` / `-i` — Path to the OpenAPI JSON file (defaults to `openapi.json`).
- `--output` / `-o` — Destination Markdown path. When omitted, the output prints to stdout.
- `--chunk-by-tag` — Split the documentation into per-tag Markdown files. Requires `--output` to point to a directory.

The generated Markdown is intended to be pasted into prompt contexts or doc portals for large language models.

When chunking is enabled, the script writes one Markdown file per tag (and `untagged.md` if any operations omit tags).

## Development

Run the converter directly from the project root:

```bash
python3 main.py -i openapi.json
```

Feel free to tweak `describe_schema_brief` or `render_component` in `main.py` to customize the schema summaries.
