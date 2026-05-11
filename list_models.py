#!/usr/bin/env python3
"""
NVIDIA NIM API - List Available Models

Displays all available models from the NVIDIA NIM API in a formatted table.
Works offline using the documented model catalog.

Requirements:
    pip install tabulate (optional, for better formatting)

Usage:
    python list_models.py                 # Show all models
    python list_models.py --filter meta   # Filter by provider
    python list_models.py --output markdown  # Markdown format
    python list_models.py --count         # Show only count
"""

import os
import sys
import argparse
import json
from typing import Optional, List, Dict

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# Complete model catalog from NVIDIA NIM API documentation
MODEL_CATALOG: List[Dict[str, str]] = [
    # Meta models
    {"id": "meta/llama-3.1-8b-instruct", "description": "Llama 3.1 8B Instruct", "context": "128K", "use_case": "General purpose, fast inference"},
    {"id": "meta/llama-3.1-70b-instruct", "description": "Llama 3.1 70B Instruct", "context": "128K", "use_case": "Complex reasoning, high quality"},
    {"id": "meta/llama-3.2-1b-instruct", "description": "Llama 3.2 1B Instruct", "context": "128K", "use_case": "Edge devices, ultra-low latency"},
    {"id": "meta/llama-3.2-3b-instruct", "description": "Llama 3.2 3B Instruct", "context": "128K", "use_case": "Mobile, low-resource"},
    {"id": "meta/llama-3.3-70b-instruct", "description": "Llama 3.3 70B Instruct", "context": "128K", "use_case": "Latest Llama, optimized"},

    # MistralAI models
    {"id": "mistralai/mistral-7b-instruct-v0.3", "description": "Mistral 7B Instruct v0.3", "context": "32K", "use_case": "Efficient general purpose"},
    {"id": "mistralai/mixtral-8x7b-instruct", "description": "Mixtral 8x7B MoE", "context": "32K", "use_case": "Balanced performance"},
    {"id": "mistralai/mixtral-8x22b-instruct", "description": "Mixtral 8x22B MoE", "context": "64K", "use_case": "High-end reasoning"},

    # Microsoft models
    {"id": "microsoft/phi-4-mini-instruct", "description": "Phi-4 Mini Instruct", "context": "16K", "use_case": "Compact, efficient"},
    {"id": "microsoft/phi-4-mini-flash-reasoning", "description": "Phi-4 Mini Flash Reasoning", "context": "16K", "use_case": "Fast reasoning tasks"},

    # Google models
    {"id": "google/gemma-7b", "description": "Gemma 7B Base", "context": "8K", "use_case": "Base model for fine-tuning"},
    {"id": "google/gemma-2-2b-it", "description": "Gemma 2 2B Instruct", "context": "8K", "use_case": "Lightweight chat"},
    {"id": "google/codegemma-7b", "description": "CodeGemma 7B", "context": "8K", "use_case": "Code generation"},

    # NVIDIA models
    {"id": "nvidia/nemotron-mini-4b-instruct", "description": "Nemotron Mini 4B", "context": "32K", "use_case": "Compact instruction following"},
    {"id": "nvidia/llama-3.1-nemotron-nano-8b-v1", "description": "Nemotron Nano 8B", "context": "128K", "use_case": "Optimized Llama variant"},

    # DeepSeek models
    {"id": "deepseek-ai/deepseek-v4-flash", "description": "DeepSeek V4 Flash", "context": "128K", "use_case": "Fast inference"},
    {"id": "deepseek-ai/deepseek-v4-pro", "description": "DeepSeek V4 Pro", "context": "128K", "use_case": "High quality"},

    # Qwen models
    {"id": "qwen/qwen2.5-coder-7b-instruct", "description": "Qwen2.5 Coder 7B", "context": "32K", "use_case": "Code generation"},
    {"id": "qwen/qwen3-coder-480b-a35b-instruct", "description": "Qwen3 Coder 480B", "context": "256K", "use_case": "Advanced coding"},

    # ByteDance models
    {"id": "bytedance/seed-oss-36b-instruct", "description": "Seed OSS 36B", "context": "32K", "use_case": "Open source large model"},

    # AbacusAI models
    {"id": "abacusai/dracarys-llama-3.1-70b-instruct", "description": "Dracarys Llama 3.1 70B", "context": "128K", "use_case": "Enhanced Llama variant"},
]


def get_provider(model_id: str) -> str:
    """Extract provider from model ID."""
    return model_id.split("/")[0] if "/" in model_id else "unknown"


def filter_models(models: List[Dict], provider: Optional[str] = None) -> List[Dict]:
    """Filter models by provider."""
    if not provider:
        return models

    return [m for m in models if provider.lower() in m["id"].lower()]


def format_markdown_table(models: List[Dict]) -> str:
    """Format as Markdown table."""
    if not models:
        return "No models found"

    lines = []
    lines.append("| Model | Description | Context | Use Case |")
    lines.append("|-------|-------------|---------|----------|")
    for m in models:
        lines.append(f"| {m['id']} | {m['description']} | {m['context']} | {m['use_case']} |")
    return "\n".join(lines)


def format_ascii_table(models: List[Dict]) -> str:
    """Format as ASCII table."""
    if not models:
        return "No models found"

    if HAS_TABULATE:
        table_data = [[m['id'], m['description'], m['context'], m['use_case']] for m in models]
        return tabulate(table_data, headers=["Model", "Description", "Context", "Use Case"], tablefmt="grid")

    # Fallback: simple format
    lines = []
    lines.append(f"{'Model':<45} | {'Description':<35} | {'Context':<10} | {'Use Case'}")
    lines.append("-" * 150)
    for m in models:
        lines.append(f"{m['id']:<45} | {m['description']:<35} | {m['context']:<10} | {m['use_case']}")
    return "\n".join(lines)


def format_json(models: List[Dict]) -> str:
    """Format as JSON."""
    return json.dumps(models, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="List NVIDIA NIM API models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python list_models.py                 # Show all models
  python list_models.py -f meta         # Filter by Meta models
  python list_models.py -o markdown     # Output as Markdown
  python list_models.py -c              # Show count only
  python list_models.py -o json         # Output as JSON
        """
    )
    parser.add_argument("--output", "-o", choices=["table", "markdown", "json"], default="table",
                       help="Output format (default: table)")
    parser.add_argument("--filter", "-f", type=str, help="Filter by provider (e.g., 'meta', 'google', 'microsoft')")
    parser.add_argument("--count", "-c", action="store_true", help="Show only count")
    args = parser.parse_args()

    # Start with full catalog
    models = MODEL_CATALOG.copy()

    # Filter by provider
    if args.filter:
        models = filter_models(models, args.filter)

    # Sort by provider then model name
    models.sort(key=lambda x: (get_provider(x['id']), x['id']))

    # Count only
    if args.count:
        print(len(models))
        return

    # Format output
    if args.output == "json":
        print(format_json(models))
    elif args.output == "markdown":
        print(format_markdown_table(models))
    else:
        print(format_ascii_table(models))


if __name__ == "__main__":
    main()
