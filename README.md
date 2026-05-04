# NVIDIA Models CLI

Fetches and lists all available models from the Nvidia API. Useful for populating configs with the latest model IDs.

## Key Features

- **Complete Model Catalog**: Fetch all available models from the NVIDIA API with pagination support
- **Filtering**: Filter models by type (e.g., `chat`, `embedding`) or family (e.g., `llama`, `mistral`)
- **Multiple Output Formats**: Table view, YAML blocks for config, or raw JSON
- **Caching**: Local cache with 1-hour TTL to reduce API calls
- **Colored Output**: Beautiful terminal output with colorama (optional)
- **Export Options**: Save YAML blocks directly to files

## Tech Stack

- **Language**: Python 3.10+
- **Dependencies**: `requests`, `colorama` (optional)
- **API**: NVIDIA API (https://integrate.api.nvidia.com/v1/models)

## Prerequisites

- Python 3.10 or higher
- NVIDIA API key (get it from https://build.nvidia.com/)
- pip (Python package manager)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/user/repo.git
cd repo
```

### 2. Install Dependencies

```bash
pip install requests
pip install colorama  # Optional, for colored output
```

### 3. Set Up Environment Variables

Export your NVIDIA API key:

```bash
export NVIDIA_API_KEY="nvapi-..."
```

**Important**: Your API key must be kept secret. Never commit it to version control.

### 4. Run the Script

```bash
python nvidia_models.py
```

## Usage Examples

### Basic Usage

List all available models:

```bash
python nvidia_models.py
```

### Filter by Model Type

Show only chat models:

```bash
python nvidia_models.py --type chat
```

Show only embedding models:

```bash
python nvidia_models.py --type embedding
```

### Filter by Model Family

Show only Llama family models:

```bash
python nvidia_models.py --family llama
```

Show only Mistral family models:

```bash
python nvidia_models.py --family mistral
```

### Combined Filters

Filter by both type and family:

```bash
python nvidia_models.py --type chat --family llama
```

### Output Formats

**YAML-only output** (suppresses table, shows only YAML block):

```bash
python nvidia_models.py --yaml-only
```

**Save YAML to file** (for Hermes config.yaml):

```bash
python nvidia_models.py --yaml-only --output models.yaml
```

**Count only** (quick check how many models match):

```bash
python nvidia_models.py --count-only
python nvidia_models.py --type chat --count-only
```

**Raw JSON dump** (for debugging or custom processing):

```bash
python nvidia_models.py --json
```

### Cache Management

The script caches API responses for 1 hour to reduce API calls.

**Bypass cache** (force fresh API call):

```bash
python nvidia_models.py --no-cache
```

**Cache location**: `.nvidia_models_cache.json` (created in current directory)

## Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--type TYPE` | Filter by model type | `--type chat` |
| `--family FAMILY` | Filter by model family | `--family llama` |
| `--yaml-only` | Show only YAML block (no table) | `--yaml-only` |
| `--output FILE` | Write YAML block to file | `--output models.yaml` |
| `--count-only` | Show only model count | `--count-only` |
| `--json` | Dump raw JSON response | `--json` |
| `--no-cache` | Bypass local cache | `--no-cache` |
| `--help` | Show help message | `--help` |

## Architecture

### Directory Structure

```
├── nvidia_models.py          # Main script
├── .nvidia_models_cache.json # Local cache (auto-generated)
├── requirements.txt          # Python dependencies (optional)
└── README.md                 # This file
```

### Request Lifecycle

1. **API Key Validation**: Checks for `NVIDIA_API_KEY` environment variable
2. **Cache Check**: Loads cached results if available and not expired (TTL: 3600s)
3. **API Fetch**: Paginates through all NVIDIA API endpoints
4. **Filtering**: Applies type and family filters
5. **Output**: Displays results in table, YAML, or JSON format

### Data Flow

```
User Input → CLI Parser → Cache Check → API Fetch (if needed) → Filter → Output
                                                    ↓
                                              Save Cache
```

### Key Components

**Cache System** (`.nvidia_models_cache.json`):
- Stores API response with timestamp
- 1-hour TTL (configurable via `CACHE_TTL`)
- Non-fatal: script works if cache write fails

**Pagination Handler**:
- Automatically follows `next_page_url` or `next` fields
- Collects all pages into single list
- Handles HTTP errors with helpful hints

**Model Family Extractor**:
- Extracts family from `attributes.model_family` field
- Falls back to parsing model ID (e.g., `meta/llama-3-70b` → `llama`)

## Environment Variables

### Required

| Variable | Description | How to Get |
|----------|-------------|------------|
| `NVIDIA_API_KEY` | NVIDIA API authentication key | https://build.nvidia.com/ → Get API Key |

### Optional

None. All other configuration is via CLI flags.

## Output Examples

### Table Output

```
Found 42 model(s):

--------------------------------------------------------------------------------
ID                                                 TYPE              FAMILY
--------------------------------------------------------------------------------
meta/llama-3-70b-instruct                          chat              llama
mistralai/mistral-large                            chat              mistral
nvidia/nema-retriever-1b                           embedding         nema
…
--------------------------------------------------------------------------------

--- YAML Copy-Paste Block ---
# NVIDIA models — paste under 'models: nvidia:' in config.yaml
- meta/llama-3-70b-instruct
- mistralai/mistral-large
- nvidia/nema-retriever-1b
--------------------------------------------------------------------------------
```

### YAML Block (for Hermes config.yaml)

```yaml
# NVIDIA models — paste under 'models: nvidia:' in config.yaml
- meta/llama-3-70b-instruct
- meta/llama-3-8b-instruct
- mistralai/mistral-large
- mistralai/mixtral-8x7b-instruct
- nvidia/nema-retriever-1b
```

### JSON Output

```json
[
  {
    "id": "meta/llama-3-70b-instruct",
    "type": "chat",
    "attributes": {
      "model_family": "llama"
    }
  },
  ...
]
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `python nvidia_models.py` | List all models (default) |
| `python nvidia_models.py --type chat` | List chat models only |
| `python nvidia_models.py --family llama` | List Llama family models |
| `python nvidia_models.py --yaml-only` | Show YAML block only |
| `python nvidia_models.py --output models.yaml` | Save YAML to file |
| `python nvidia_models.py --count-only` | Show model count |
| `python nvidia_models.py --json` | Dump raw JSON |
| `python nvidia_models.py --no-cache` | Force fresh API call |

## Troubleshooting

### Error: `NVIDIA_API_KEY environment variable not set`

**Solution**: Export your API key before running:

```bash
export NVIDIA_API_KEY="nvapi-..."
```

### Error: `HTTP Error: 401 Unauthorized`

**Cause**: Invalid or expired API key.

**Solution**:
1. Verify your API key is correct
2. Check if it has expired (keys may have expiration dates)
3. Generate a new key at https://build.nvidia.com/

### Error: `HTTP Error: 403 Forbidden`

**Cause**: Your account lacks permission to access the model catalog endpoint.

**Solution**:
1. Verify your NVIDIA API access level
2. Ensure you have permission to list models
3. Contact NVIDIA support if needed

### Error: `HTTP Error: 429 Too Many Requests`

**Cause**: Rate limited by the API.

**Solution**:
1. Wait a moment and try again
2. Use `--no-cache` sparingly
3. The script caches results for 1 hour by default

### Error: `Request failed: ...`

**Cause**: Network issue or API downtime.

**Solution**:
1. Check your internet connection
2. Verify NVIDIA API status
3. Try again later

### Cache Issues

**Problem**: Cache file corrupted or outdated.

**Solution**:
```bash
# Delete cache file
rm .nvidia_models_cache.json

# Or bypass cache for one run
python nvidia_models.py --no-cache
```

### No Models Found

**Cause**: Filters too restrictive or API returned empty results.

**Solution**:
1. Run without filters to see all models
2. Check filter spelling (`llama` not `llama-3`)
3. Verify API key has correct permissions

## Integration with Hermes Agent

This script is designed to work with the Hermes Agent configuration system.

### Step 1: Fetch Models

```bash
python nvidia_models.py --yaml-only --output nvidia_models.yaml
```

### Step 2: Add to Hermes config.yaml

Open your Hermes `config.yaml` and add the models under the NVIDIA provider:

```yaml
models:
  nvidia:
    - meta/llama-3-70b-instruct
    - meta/llama-3-8b-instruct
    - mistralai/mistral-large
```

### Step 3: Use in Hermes

Now you can reference NVIDIA models in your Hermes workflows:

```yaml
agent:
  model: nvidia/meta/llama-3-70b-instruct
```

## Performance Considerations

- **Caching**: Reduces API calls; cache lasts 1 hour by default
- **Pagination**: Automatically handles large model lists
- **Timeout**: 30-second timeout per API request
- **Non-blocking**: Cache write failures are ignored (non-fatal)

## Security Notes

- **Never commit API keys** to version control
- Use environment variables for sensitive data
- The `.nvidia_models_cache.json` file does not contain your API key
- Consider adding `.nvidia_models_cache.json` to `.gitignore`

## Contributing

To extend this script:

1. **Add new filters**: Modify `filter_models()` function
2. **Change output format**: Add new output helper functions
3. **Adjust cache TTL**: Modify `CACHE_TTL` constant (default: 3600 seconds)
4. **Custom API endpoints**: Update `NVIDIA_MODELS_BASE_URL`

## License

This project is provided as-is for use with the NVIDIA API.

## Resources

- **NVIDIA API Documentation**: https://docs.api.nvidia.com/
- **Get API Key**: https://build.nvidia.com/
- **Hermes Agent**: https://hermes-agent.nousresearch.com/docs
- **Python Requests**: https://docs.python-requests.org/
- **Colorama**: https://pypi.org/project/colorama/

## Version History

- **v1.0**: Initial release
  - Basic model listing
  - Type and family filtering
  - YAML output for Hermes config
  - Local caching with 1-hour TTL
  - Colored terminal output
  - JSON export option
