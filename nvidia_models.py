#!/usr/bin/env python3
"""
Fetches and lists all available models from the Nvidia API.
Useful for populating Hermes config.yaml with the latest model IDs.

Requirements:
 pip install requests

Optional (for colored output):
 pip install colorama

Usage:
 export NVIDIA_API_KEY="nvapi-..."
 python list_nvidia_models.py
 python list_nvidia_models.py --type chat
 python list_nvidia_models.py --family llama
 python list_nvidia_models.py --yaml-only --output models.yaml
 python list_nvidia_models.py --count-only
 python list_nvidia_models.py --json
 python list_nvidia_models.py --no-cache
 python list_nvidia_models.py --debug
"""

import os
import sys
import json
import time
import argparse
import pathlib
import requests

# ── Optional colorama ─────────────────────────────────────────────────────────
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    COLOR = True
except ImportError:
    COLOR = False

    class _Noop:
        def __getattr__(self, _):
            return ""

    Fore = Style = _Noop()

# ── Cache config ──────────────────────────────────────────────────────────────
CACHE_FILE = pathlib.Path(".nvidia_models_cache.json")
CACHE_TTL = 3600  # seconds (1 hour)

NVIDIA_MODELS_BASE_URL = "https://integrate.api.nvidia.com/v1/models"


# ── Cache helpers ─────────────────────────────────────────────────────────────
def load_cache() -> list | None:
    """Return cached model list if fresh, else None."""
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text())
        age = time.time() - data.get("ts", 0)
        if age < CACHE_TTL:
            remaining = int(CACHE_TTL - age)
            print(
                f"{Fore.CYAN}Using cached results "
                f"(expires in {remaining}s). Pass --no-cache to refresh.{Style.RESET_ALL}"
            )
            return data["models"]
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def save_cache(models: list) -> None:
    try:
        CACHE_FILE.write_text(json.dumps({"ts": time.time(), "models": models}))
    except OSError:
        pass  # Non-fatal: cache write failure is ignorable


# ── API fetch (with pagination) ───────────────────────────────────────────────
def fetch_all_models(api_key: str) -> list:
    """Fetch every page of models from the NVIDIA API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    models: list = []
    url: str | None = NVIDIA_MODELS_BASE_URL
    page = 1

    while url:
        print(f"Fetching page {page}: {url} ...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            _handle_http_error(exc, response)
            sys.exit(1)
        except requests.exceptions.RequestException as exc:
            print(f"{Fore.RED}Request failed: {exc}{Style.RESET_ALL}")
            sys.exit(1)

        data = response.json()
        page_models = data.get("data", [])
        models.extend(page_models)

        # Advance to next page if the API signals one.
        # Adjust field name to match whatever the real NVIDIA pagination envelope uses.
        url = data.get("next_page_url") or data.get("next") or None
        page += 1

    return models


def _handle_http_error(exc: requests.exceptions.HTTPError, response: requests.Response) -> None:
    print(f"{Fore.RED}HTTP Error: {exc}{Style.RESET_ALL}")
    try:
        body = response.text
    except Exception:
        body = "<no body>"
    print(f"Response body: {body}")
    status = getattr(response, "status_code", None)
    if status == 401:
        print("Hint: Your API key may be invalid or expired.")
    elif status == 403:
        print("Hint: Your account may not have access to the model catalog endpoint.")
    elif status == 429:
        print("Hint: Rate limited — wait a moment and try again.")

# ── Model helpers ─────────────────────────────────────────────────────────────
def _family(model: dict) -> str:
    """Extract model family from attributes or parse from model ID."""
    attrs = model.get("attributes") or {}
    family = attrs.get("model_family", "") if isinstance(attrs, dict) else ""
    if not family:
        model_id: str = model.get("id", "")
        if "/" in model_id:
            parts = model_id.split("/")
            if len(parts) > 1:
                family = parts[1].split("-")[0]
    return family


def _provider(model: dict) -> str:
    """Extract provider/owner from model data."""
    # Try owned_by field first
    owned_by = model.get("owned_by")
    if owned_by:
        return str(owned_by)
    
    # Parse from model ID (e.g., "meta/llama-3-70b" -> "meta")
    model_id: str = model.get("id", "")
    if "/" in model_id:
        return model_id.split("/")[0]
    
    return "unknown"


def filter_models(models: list, type_filter: str | None, family_filter: str | None) -> list:
    if type_filter:
        # Filter by provider (owned_by) or model ID contains the filter
        models = [m for m in models if type_filter.lower() in _provider(m).lower() or type_filter.lower() in m.get("id", "").lower()]
    if family_filter:
        models = [m for m in models if family_filter.lower() in _family(m).lower()]
    return models


# ── Output helpers ────────────────────────────────────────────────────────────
COL_ID = 50
COL_TYPE = 15
COL_FAMILY = 20

DIVIDER = "-" * (COL_ID + COL_TYPE + COL_FAMILY + 4)


def print_table(models: list) -> None:
    print(f"\n{Fore.GREEN}Found {len(models)} model(s):{Style.RESET_ALL}\n")
    print(DIVIDER)
    header = (
        f"{Fore.YELLOW}{'ID':<{COL_ID}} {'PROVIDER':<{COL_TYPE}} {'FAMILY':<{COL_FAMILY}}{Style.RESET_ALL}"
    )
    print(header)
    print(DIVIDER)

    for model in models:
        model_id: str = model.get("id", "unknown")
        provider: str = _provider(model)
        family: str = _family(model)

        # Truncate long IDs with ellipsis so the table stays aligned
        display_id = model_id if len(model_id) <= COL_ID else model_id[: COL_ID - 1] + "…"
        print(f"{display_id:<{COL_ID}} {provider:<{COL_TYPE}} {family:<{COL_FAMILY}}")

    print(DIVIDER)


def build_yaml_block(models: list) -> str:
    lines = ["# NVIDIA models — paste under 'models: nvidia:' in config.yaml"]
    for model in models:
        model_id = model.get("id", "unknown")
        lines.append(f"- {model_id}")
    return "\n".join(lines)


def print_debug_info(models: list) -> None:
    """Print first model's full structure for debugging."""
    if not models:
        return
    print(f"\n{Fore.CYAN}=== Debug: First Model Structure ==={Style.RESET_ALL}")
    print(json.dumps(models[0], indent=2))
    print(f"{Fore.CYAN}====================================={Style.RESET_ALL}\n")


def print_yaml_block(models: list) -> None:
    print(f"\n{Fore.CYAN}--- YAML Copy-Paste Block ---{Style.RESET_ALL}")
    print(build_yaml_block(models))
    print(f"{Fore.CYAN}{DIVIDER}{Style.RESET_ALL}")


def write_output(content: str, path: str) -> None:
    out = pathlib.Path(path)
    out.write_text(content)
    print(f"{Fore.GREEN}Written to {out.resolve()}{Style.RESET_ALL}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="List NVIDIA API models and generate config.yaml snippets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--type", metavar="TYPE", help="Filter by provider or model name (e.g. google, meta, llama)")
    p.add_argument("--family", metavar="FAMILY", help="Filter by model family (e.g. llama, mistral)")
    p.add_argument(
        "--yaml-only",
        action="store_true",
        help="Print only the YAML block (suppresses table)",
    )
    p.add_argument("--output", metavar="FILE", help="Write YAML block to this file")
    p.add_argument(
        "--count-only",
        action="store_true",
        help="Print only the model count and exit",
    )
    p.add_argument(
        "--json",
        dest="dump_json",
        action="store_true",
        help="Dump raw API response as JSON (ignores filters)",
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the local cache and always hit the API",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Print first model's full JSON structure for debugging",
    )
    return p


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # API key
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print(
            f"{Fore.RED}Error: NVIDIA_API_KEY environment variable not set.\n"
            f"Please run: export NVIDIA_API_KEY='nvapi-...'{Style.RESET_ALL}"
        )
        sys.exit(1)

    # Fetch (with optional cache)
    models: list | None = None
    if not args.no_cache and not args.dump_json:
        models = load_cache()

    if models is None:
        models = fetch_all_models(api_key)
        if not args.dump_json:
            save_cache(models)

    if not models:
        print("No models found. Check your API key permissions.")
        return

    # --json: dump raw and exit
    if args.dump_json:
        print(json.dumps(models, indent=2))
        return

    # Sort
    models.sort(key=lambda x: x.get("id", ""))

    # --count-only (before filtering so you see total)
    if args.count_only:
        filtered = filter_models(models, args.type, args.family)
        scope = "total"
        if args.type or args.family:
            parts = []
            if args.type:
                parts.append(f"type={args.type}")
            if args.family:
                parts.append(f"family={args.family}")
            scope = ", ".join(parts)
        print(f"{len(filtered)} model(s) [{scope}]")
        return

    # Filter
    models = filter_models(models, args.type, args.family)
    if not models:
        print("No models matched your filters.")
        return

    # Debug: show first model structure
    if args.debug:
        print_debug_info(models)

    # Output
    yaml_block = build_yaml_block(models)

    if not args.yaml_only:
        print_table(models)

    if args.output:
        write_output(yaml_block, args.output)
    else:
        print_yaml_block(models)


if __name__ == "__main__":
    main()
