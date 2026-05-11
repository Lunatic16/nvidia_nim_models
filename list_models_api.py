#!/usr/bin/env python3
"""
NVIDIA NIM API - List Available Models (Live API)

Retrieves and displays all available models from the NVIDIA NIM API
in a formatted table by querying the live API endpoint.

Requirements:
    pip install requests tabulate

Usage:
    export NVIDIA_API_KEY="nvapi-xxx"
    python list_models_api.py
    python list_models_api.py --output markdown  # table, markdown, json
    python list_models_api.py --filter meta     # Filter by provider
"""

import os
import sys
import argparse
import json
import re
from typing import Optional, List, Dict, Any

try:
    import requests
except ImportError:
    print("Installing missing dependency: requests")
    os.system("pip install requests")
    import requests

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# Enhanced metadata with fallbacks
MODEL_METADATA = {
    # Meta models
    "meta/llama-3.1-8b-instruct": {"description": "Llama 3.1 8B Instruct", "context": "128K", "use_case": "General purpose, fast inference"},
    "meta/llama-3.1-70b-instruct": {"description": "Llama 3.1 70B Instruct", "context": "128K", "use_case": "Complex reasoning, high quality"},
    "meta/llama-3.2-1b-instruct": {"description": "Llama 3.2 1B Instruct", "context": "128K", "use_case": "Edge devices, ultra-low latency"},
    "meta/llama-3.2-3b-instruct": {"description": "Llama 3.2 3B Instruct", "context": "128K", "use_case": "Mobile, low-resource"},
    "meta/llama-3.3-70b-instruct": {"description": "Llama 3.3 70B Instruct", "context": "128K", "use_case": "Latest Llama, optimized"},
    # MistralAI
    "mistralai/mistral-7b-instruct-v0.3": {"description": "Mistral 7B Instruct v0.3", "context": "32K", "use_case": "Efficient general purpose"},
    "mistralai/mixtral-8x7b-instruct": {"description": "Mixtral 8x7B MoE", "context": "32K", "use_case": "Balanced performance"},
    "mistralai/mixtral-8x22b-instruct": {"description": "Mixtral 8x22B MoE", "context": "64K", "use_case": "High-end reasoning"},
    # Microsoft
    "microsoft/phi-4-mini-instruct": {"description": "Phi-4 Mini Instruct", "context": "16K", "use_case": "Compact, efficient"},
    "microsoft/phi-4-mini-flash-reasoning": {"description": "Phi-4 Mini Flash Reasoning", "context": "16K", "use_case": "Fast reasoning tasks"},
    # Google
    "google/gemma-7b": {"description": "Gemma 7B Base", "context": "8K", "use_case": "Base model for fine-tuning"},
    "google/gemma-2-2b-it": {"description": "Gemma 2 2B Instruct", "context": "8K", "use_case": "Lightweight chat"},
    "google/codegemma-7b": {"description": "CodeGemma 7B", "context": "8K", "use_case": "Code generation"},
    # NVIDIA
    "nvidia/nemotron-mini-4b-instruct": {"description": "Nemotron Mini 4B", "context": "32K", "use_case": "Compact instruction following"},
    "nvidia/llama-3.1-nemotron-nano-8b-v1": {"description": "Nemotron Nano 8B", "context": "128K", "use_case": "Optimized Llama variant"},
    # DeepSeek
    "deepseek-ai/deepseek-v4-flash": {"description": "DeepSeek V4 Flash", "context": "128K", "use_case": "Fast inference"},
    "deepseek-ai/deepseek-v4-pro": {"description": "DeepSeek V4 Pro", "context": "128K", "use_case": "High quality"},
    # Qwen
    "qwen/qwen2.5-coder-7b-instruct": {"description": "Qwen2.5 Coder 7B", "context": "32K", "use_case": "Code generation"},
    "qwen/qwen3-coder-480b-a35b-instruct": {"description": "Qwen3 Coder 480B", "context": "256K", "use_case": "Advanced coding"},
    # ByteDance
    "bytedance/seed-oss-36b-instruct": {"description": "Seed OSS 36B", "context": "32K", "use_case": "Open source large model"},
    # AbacusAI
    "abacusai/dracarys-llama-3.1-70b-instruct": {"description": "Dracarys Llama 3.1 70B", "context": "128K", "use_case": "Enhanced Llama variant"},
}


def get_api_key() -> str:
    """Get API key from environment."""
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("Error: NVIDIA_API_KEY environment variable not set")
        print("Set it with: export NVIDIA_API_KEY='nvapi-xxx'")
        print("\nGet your API key from: https://ngc.nvidia.com")
        sys.exit(1)
    return api_key


def parse_model_id(model_id: str) -> Dict[str, str]:
    """Parse model ID to extract provider, name, and size info."""
    parts = model_id.split("/")
    provider = parts[0] if parts else "unknown"
    name = parts[1] if len(parts) > 1 else model_id

    # Extract size pattern (e.g., "70b", "8b", "480b")
    size_match = re.search(r'(\d+(?:\.\d+)?)(?:b|b-instruct|instruct)', name.lower())
    size = size_match.group(0).upper() if size_match else ""

    # Extract context from name patterns
    context = ""
    if "coder" in name.lower():
        context = "Code generation"
    elif "vision" in name.lower() or "multimodal" in name.lower():
        context = "Multimodal"
    elif "embed" in name.lower():
        context = "Embedding"
    elif "guard" in name.lower() or "safety" in name.lower():
        context = "Safety/Guardrails"
    elif "reason" in name.lower() or "thinking" in name.lower():
        context = "Reasoning"
    elif "translate" in name.lower():
        context = "Translation"
    elif "chat" in name.lower() or "instruct" in name.lower():
        context = "Chat/Instruct"

    return {
        "provider": provider,
        "name": name,
        "size": size,
        "context_type": context
    }


def fetch_models(api_key: str) -> List[Dict]:
    """Fetch available models from NVIDIA API."""
    url = "https://integrate.api.nvidia.com/v1/models"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            if e.response.status_code == 401:
                print("\nAuthentication failed. Check your API key.")
            elif e.response.status_code == 403:
                print("\nAccess denied. Verify your API key has 'AI Foundation Models and Endpoints' access.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models: {e}")
        sys.exit(1)


def extract_context_from_name(name: str) -> str:
    """Extract context window size from model name if present."""
    # Patterns like "128k", "32k", "256k"
    match = re.search(r'(\d+)k(?:-|\s|$|\.|\))', name.lower())
    if match:
        return f"{match.group(1)}K"
    return ""


def generate_description(model_id: str, model_data: Dict) -> str:
    """Generate a description from model ID and data."""
    parsed = parse_model_id(model_id)
    name = parsed["name"]

    # Check known metadata first
    if model_id in MODEL_METADATA:
        return MODEL_METADATA[model_id]["description"]

    # Generate from name patterns
    parts = name.replace("-", " ").replace("_", " ").split()

    # Build description from parts
    description_parts = []

    # Add provider name for clarity
    if parsed["provider"]:
        description_parts.append(parsed["provider"].capitalize())

    # Add model family
    if "llama" in name.lower():
        if "3.3" in name.lower():
            description_parts = ["Llama 3.3"]
        elif "3.2" in name.lower():
            description_parts = ["Llama 3.2"]
        elif "3.1" in name.lower():
            description_parts = ["Llama 3.1"]
        elif "3" in name.lower():
            description_parts = ["Llama 3"]
        elif "guard" in name.lower():
            description_parts = ["Llama Guard"]

    if "nemotron" in name.lower():
        if "nano" in name.lower():
            description_parts = ["Nemotron Nano"]
        elif "mini" in name.lower():
            description_parts = ["Nemotron Mini"]
        elif "super" in name.lower():
            description_parts = ["Nemotron Super"]
        elif "ultra" in name.lower():
            description_parts = ["Nemotron Ultra"]
        else:
            description_parts = ["Nemotron"]

    if "gemma" in name.lower():
        if "code" in name.lower():
            description_parts = ["CodeGemma"]
        else:
            description_parts = ["Gemma"]

    if "phi" in name.lower():
        description_parts = ["Phi"]

    if "mistral" in name.lower() or "mixtral" in name.lower():
        description_parts = [" ".join(name.replace("-", " ").replace("_", " ").title().split()[:3])]

    if "qwen" in name.lower():
        description_parts = ["Qwen"]

    if "deepseek" in name.lower():
        description_parts = ["DeepSeek"]

    # Add type indicators
    if "instruct" in name.lower() or "chat" in name.lower():
        description_parts.append("Instruct")
    elif "embed" in name.lower():
        description_parts.append("Embedding")
    elif "coder" in name.lower() or "code" in name.lower():
        description_parts.append("Code")
    elif "vision" in name.lower() or "vl" in name.lower():
        description_parts.append("Vision")
    elif "guard" in name.lower() or "safety" in name.lower():
        description_parts.append("Safety")
    elif "reason" in name.lower() or "thinking" in name.lower():
        description_parts.append("Reasoning")
    elif "translate" in name.lower():
        description_parts.append("Translation")

    # If we have parts, join them
    if description_parts:
        return " ".join(description_parts)

    # Fallback: capitalize the model name
    return name.replace("-", " ").replace("_", " ").title()


def generate_use_case(model_id: str, model_data: Dict) -> str:
    """Generate use case from model characteristics."""
    name = model_id.lower()

    # Check known metadata first
    if model_id in MODEL_METADATA:
        return MODEL_METADATA[model_id]["use_case"]

    # Determine use case from patterns
    if any(x in name for x in ["coder", "code", "codellama", "codegemma"]):
        return "Code generation"
    elif "embed" in name:
        return "Text embedding"
    elif "vision" in name or "vl" in name or "multimodal" in name:
        return "Multimodal (vision + text)"
    elif "guard" in name or "safety" in name:
        return "Content safety / Guardrails"
    elif "reason" in name or "thinking" in name:
        return "Complex reasoning"
    elif "translate" in name:
        return "Translation"
    elif "recruit" in name or "rerank" in name:
        return "Reranking / Search"
    elif "instruct" in name or "chat" in name:
        # Check size for tier
        if any(x in name for x in ["70b", "80b", "90b", "120b", "253b", "480b"]):
            return "High-quality chat / Complex tasks"
        elif any(x in name for x in ["1b", "2b", "3b", "4b", "7b", "8b"]):
            return "Fast inference / General chat"
        else:
            return "General purpose chat"
    elif "nemoretriever" in name or "retriever" in name:
        return "RAG / Retrieval"
    elif "parse" in name:
        return "Document parsing"
    else:
        return "General purpose"


def enrich_model(model: Dict) -> Dict:
    """Add metadata to model info."""
    model_id = model.get("id", "")
    metadata = MODEL_METADATA.get(model_id, {})
    parsed = parse_model_id(model_id)

    # Get description from metadata or generate
    description = metadata.get("description") or generate_description(model_id, model)

    # Get context window
    context = metadata.get("context", "")
    if not context:
        # Try to extract from model name
        context = extract_context_from_name(model_id)
        if not context:
            # Use heuristics based on model family
            if "llama-3" in model_id.lower() or "nemotron" in model_id.lower():
                context = "128K"  # Most modern Llama models
            elif "gemma" in model_id.lower():
                context = "8K"
            elif "phi-4" in model_id.lower():
                context = "16K"
            elif "mistral" in model_id.lower() or "mixtral" in model_id.lower():
                context = "32K"
            elif "qwen3" in model_id.lower():
                context = "256K"
            elif "deepseek" in model_id.lower():
                context = "128K"

    return {
        "model": model_id,
        "description": description,
        "context": context if context else "N/A",
        "use_case": generate_use_case(model_id, model),
        "provider": parsed["provider"],
        "size": parsed.get("size", ""),
    }


def filter_models(models: List[Dict], provider: Optional[str] = None) -> List[Dict]:
    """Filter models by provider."""
    if not provider:
        return models

    return [m for m in models if provider.lower() in m.get("model", "").lower()]


def format_markdown_table(models: List[Dict]) -> str:
    """Format as Markdown table."""
    if not models:
        return "No models found"

    lines = []
    lines.append("| Model | Description | Context | Use Case |")
    lines.append("|-------|-------------|---------|----------|")
    for m in models:
        lines.append(f"| {m['model']} | {m['description']} | {m['context']} | {m['use_case']} |")
    return "\n".join(lines)


def format_ascii_table(models: List[Dict]) -> str:
    """Format as ASCII table."""
    if not models:
        return "No models found"

    if HAS_TABULATE:
        table_data = [[m['model'], m['description'], m['context'], m['use_case']] for m in models]
        return tabulate(table_data, headers=["Model", "Description", "Context", "Use Case"], tablefmt="grid")
    else:
        # Fallback: simple pipe format
        lines = []
        lines.append(f"| {'Model':<50} | {'Description':<40} | {'Context':<10} | {'Use Case'}")
        lines.append("|" + "-"*52 + "|" + "-"*42 + "|" + "-"*12 + "|" + "-"*40)
        for m in models:
            lines.append(f"| {m['model']:<50} | {m['description']:<40} | {m['context']:<10} | {m['use_case']}")
        return "\n".join(lines)


def format_json_output(models: List[Dict]) -> str:
    """Format as JSON."""
    return json.dumps(models, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="List NVIDIA NIM API models (live from API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python list_models_api.py                 # Show all models
  python list_models_api.py -f meta         # Filter by Meta models
  python list_models_api.py -o markdown     # Output as Markdown
  python list_models_api.py -c              # Show count only
  python list_models_api.py -o json         # Output as JSON

Get your API key from: https://ngc.nvidia.com
        """
    )
    parser.add_argument("--output", "-o", choices=["table", "markdown", "json"], default="table",
                       help="Output format (default: table)")
    parser.add_argument("--filter", "-f", type=str, help="Filter by provider (e.g., 'meta', 'google', 'microsoft')")
    parser.add_argument("--count", "-c", action="store_true", help="Show only count")
    args = parser.parse_args()

    # Get API key
    api_key = get_api_key()

    # Fetch models from API
    models_raw = fetch_models(api_key)

    # Enrich with metadata and generated info
    models = [enrich_model(m) for m in models_raw]

    # Filter by provider if specified
    if args.filter:
        models = filter_models(models, args.filter)

    # Sort by provider then model name
    models.sort(key=lambda x: (x['provider'], x['model']))

    # Count only
    if args.count:
        print(len(models))
        return

    # Format and output
    if args.output == "json":
        print(format_json_output(models))
    elif args.output == "markdown":
        print(format_markdown_table(models))
    else:
        print(format_ascii_table(models))


if __name__ == "__main__":
    main()
