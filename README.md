<h1 align="center"><a href="https://github.com/topics/nvidia-nim">NVIDIA NIM Models<br><img height="150" alt="NVIDIA" src="https://raw.githubusercontent.com/github/explore/refs/heads/main/topics/nvidia/nvidia.png"></a></h1>

# NVIDIA NIM API Scripts

Utility scripts for interacting with the NVIDIA NIM API.

---

## Table of Contents

- [list_models_api.py](#list_models_api) - Live API model listing with metadata extraction
- [list_models.py](#list_models) - Offline model catalog reference
- [Installation](#installation)
- [Usage Examples](#usage-examples)

---

## list_models_api.py

**Purpose:** Retrieves and displays all available models from the NVIDIA NIM API by querying the live `/v1/models` endpoint.

**Features:**
- Queries live API at `https://integrate.api.nvidia.com/v1/models`
- Auto-generates descriptions, context windows, and use cases from model naming patterns
- Supports filtering by provider (meta, google, mistralai, etc.)
- Multiple output formats: ASCII table, Markdown, JSON
- Handles 130+ models from multiple providers

### Requirements

```bash
pip install requests tabulate
```

- `requests` - HTTP library for API calls
- `tabulate` - Pretty table formatting (optional, falls back to simple format if not installed)

### Setup

```bash
# Set your NVIDIA API key
export NVIDIA_API_KEY="nvapi-xxx"
```

Get your API key from: https://ngc.nvidia.com

### Usage

```bash
# Show all models in ASCII table format
python list_models_api.py

# Show only model count
python list_models_api.py --count

# Filter by provider
python list_models_api.py --filter meta
python list_models_api.py -f google
python list_models_api.py -f mistralai

# Output as Markdown table
python list_models_api.py --output markdown

# Output as JSON
python list_models_api.py --output json

# Combine filter and output format
python list_models_api.py -f meta -o markdown
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table` (default), `markdown`, `json` |
| `--filter` | `-f` | Filter by provider name (e.g., `meta`, `google`, `microsoft`) |
| `--count` | `-c` | Show only the count of models |

### Output Format

Default output is an ASCII table:

```
| Model                                | Description                    | Context    | Use Case                           |
|--------------------------------------|--------------------------------|------------|------------------------------------|
| meta/llama-3.1-8b-instruct           | Llama 3.1 8B Instruct          | 128K       | General purpose, fast inference    |
| meta/llama-3.1-70b-instruct          | Llama 3.1 70B Instruct         | 128K       | Complex reasoning, high quality    |
| google/gemma-7b                      | Gemma 7B Base                  | 8K         | Base model for fine-tuning         |
| mistralai/mistral-7b-instruct-v0.3   | Mistral 7B Instruct v0.3       | 32K        | Efficient general purpose          |
```

### How It Works

1. **API Call:** Fetches model list from `GET /v1/models`
2. **Metadata Enrichment:** For each model, generates:
   - **Description:** Parsed from model name using pattern matching
   - **Context:** Extracted from name patterns or inferred from model family
   - **Use Case:** Determined by model characteristics
3. **Filtering:** Optional provider-based filtering
4. **Formatting:** Output in requested format

### Description Generation Logic

The script uses intelligent pattern matching:

**Model Family Detection:**
- `llama` → "Llama 3.1", "Llama 3.2", "Llama 3.3", "Llama Guard"
- `nemotron` → "Nemotron Nano", "Nemotron Mini", "Nemotron"
- `gemma` → "Gemma", "CodeGemma"
- `phi` → "Phi"
- `mistral`/`mixtral` → "Mistral", "Mixtral"
- `qwen` → "Qwen"
- `deepseek` → "DeepSeek"

**Type Detection:**
- `instruct`, `chat` → "Instruct"
- `embed` → "Embedding"
- `coder`, `code` → "Code"
- `vision`, `vl` → "Vision"
- `guard`, `safety` → "Safety"
- `reason`, `thinking` → "Reasoning"

**Context Window Heuristics:**
- Llama-3.x models → 128K
- Gemma → 8K
- Phi-4 → 16K
- Mistral/Mixtral → 32K
- Qwen3 → 256K
- DeepSeek → 128K

### Use Case Detection

| Pattern | Use Case |
|---------|----------|
| `coder`, `code` | Code generation |
| `embed` | Text embedding |
| `vision`, `vl`, `multimodal` | Multimodal (vision + text) |
| `guard`, `safety` | Content safety / Guardrails |
| `reason`, `thinking` | Complex reasoning |
| `translate` | Translation |
| `rerank`, `recruit` | Reranking / Search |
| `instruct`, `chat` (large models 70b+) | High-quality chat / Complex tasks |
| `instruct`, `chat` (small models 1b-8b) | Fast inference / General chat |
| Default | General purpose |

### Error Handling

| Error | Message | Solution |
|-------|---------|----------|
| `401 Unauthorized` | "Authentication failed. Check your API key." | Verify API key is correct and not expired |
| `403 Forbidden` | "Access denied." | Ensure API key has 'AI Foundation Models and Endpoints' access |
| Missing API key | "NVIDIA_API_KEY environment variable not set" | Run `export NVIDIA_API_KEY='nvapi-xxx'` |

### Example Output

```bash
$ python list_models_api.py -f meta --count
12
```

```bash
$ python list_models_api.py -f meta -o markdown
| Model | Description | Context | Use Case |
|-------|-------------|---------|----------|
| meta/codellama-70b | Meta Code | N/A | Code generation |
| meta/llama-3.1-70b-instruct | Llama 3.1 70B Instruct | 128K | Complex reasoning, high quality |
| meta/llama-3.1-8b-instruct | Llama 3.1 8B Instruct | 128K | General purpose, fast inference |
| meta/llama-3.2-11b-vision-instruct | Llama 3.2 Instruct | 128K | Multimodal (vision + text) |
| meta/llama-3.2-1b-instruct | Llama 3.2 1B Instruct | 128K | Edge devices, ultra-low latency |
| meta/llama-3.2-3b-instruct | Llama 3.2 3B Instruct | 128K | Mobile, low-resource |
| meta/llama-3.2-90b-vision-instruct | Llama 3.2 Instruct | 128K | Multimodal (vision + text) |
| meta/llama-3.3-70b-instruct | Llama 3.3 70B Instruct | 128K | Latest Llama, optimized |
| meta/llama-4-maverick-17b-128e-instruct | Meta Instruct | N/A | Fast inference / General chat |
| meta/llama-guard-4-12b | Llama Guard Safety | N/A | Content safety / Guardrails |
| meta/llama2-70b | Meta | N/A | General purpose |
```

---

## list_models.py

**Purpose:** Offline reference script that displays models from a static catalog without requiring API access.

**Features:**
- No API key required
- Works offline
- Pre-populated with 21 known models
- Same output formats as `list_models_api.py`

### Usage

```bash
# Show all models
python list_models.py

# Filter by provider
python list_models.py --filter meta

# Output as Markdown
python list_models.py --output markdown

# Show count only
python list_models.py --count
```

### When to Use

| Script | Use Case |
|--------|----------|
| `list_models_api.py` | You have an API key and want live data |
| `list_models.py` | You need offline access or quick reference |

---

## Installation

### Full Setup (Recommended)

```bash
# Install dependencies
pip install requests tabulate

# Set API key
export NVIDIA_API_KEY="nvapi-xxx"
```

### Minimal Setup

```bash
# Install only requests (tabulate is optional)
pip install requests

# Set API key
export NVIDIA_API_KEY="nvapi-xxx"
```

Without `tabulate`, output falls back to simple pipe format.

---

## Usage Examples

### Basic Usage

```bash
# Get API key from NGC Dashboard
export NVIDIA_API_KEY="nvapi-xxx"

# List all available models
python list_models_api.py

# Count models by provider
python list_models_api.py -f meta --count
python list_models_api.py -f google --count
python list_models_api.py -f mistralai --count
```

### Finding the Right Model

```bash
# Find code generation models
python list_models_api.py | grep -i code

# Find small/fast models (<8B)
python list_models_api.py | grep -E "1b|2b|3b|4b|7b|8b"

# Find vision/multimodal models
python list_models_api.py | grep -i vision
```

### Exporting Model List

```bash
# Export to JSON
python list_models_api.py -o json > models.json

# Export to Markdown
python list_models_api.py -o markdown > models.md

# Export to text file
python list_models_api.py > models.txt
```

### Integration Examples

**Python SDK Integration:**

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)

# Get model list
models = client.models.list()
for model in models:
    print(f"{model.id}: {model.owned_by}")
```

**cURL Integration:**

```bash
curl -s https://integrate.api.nvidia.com/v1/models \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Accept: application/json" \
  | jq '.data[].id'
```

---

## Troubleshooting

### "No module named 'requests'"

```bash
pip install requests
```

### "No module named 'tabulate'"

```bash
pip install tabulate
# Or run without it (simple format will be used)
```

### "NVIDIA_API_KEY environment variable not set"

```bash
export NVIDIA_API_KEY="nvapi-xxx"
# Replace with your actual API key
```

### "Authentication failed"

1. Verify your API key is correct
2. Check that it hasn't expired
3. Ensure it has 'AI Foundation Models and Endpoints' access

### "Access denied"

Your API key may not have the required permissions. Check NGC dashboard for access settings.

---

## Related Documentation

- [Main Documentation](../README.md)
- [API Reference](../reference/endpoints.md)
- [Models Catalog](../models/README.md)
- [Getting Started Guide](../guides/getting-started.md)

## License

NVIDIA AI Enterprise EULA - https://www.nvidia.com/en-us/data-center/products/nvidia-ai-enterprise/eula/
