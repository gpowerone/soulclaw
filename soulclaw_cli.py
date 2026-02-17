#!/usr/bin/env python3
"""
SoulClaw CLI - Generate Openclaw-compatible agent definition files using AI.

This tool collects information about your agent and uses an AI provider
(OpenAI, Claude, Grok, or Gemini) to generate four Markdown files:
SOUL.md, IDENTITY.md, GOALS.md, and USER.md.
"""

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from string import Template

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _config_dir() -> Path:
    """Return the per-user config directory (cross-platform)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_path = base / "soulclaw"
    config_path.mkdir(parents=True, exist_ok=True)
    return config_path


def _config_file() -> Path:
    return _config_dir() / "config.json"


def load_config() -> dict:
    """Load the stored configuration, or return an empty dict."""
    path = _config_file()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict) -> None:
    """Persist configuration to the per-user config file."""
    path = _config_file()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print(f"Configuration saved to {path}")


# ---------------------------------------------------------------------------
# Supported providers
# ---------------------------------------------------------------------------

PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-4o",
    },
    "claude": {
        "label": "Anthropic Claude",
        "default_model": "claude-sonnet-4-20250514",
    },
    "grok": {
        "label": "xAI Grok",
        "default_model": "grok-3",
    },
    "gemini": {
        "label": "Google Gemini",
        "default_model": "gemini-2.0-flash",
    },
}


# ---------------------------------------------------------------------------
# AI call dispatcher
# ---------------------------------------------------------------------------

def call_ai(provider: str, model: str, api_key: str, prompt: str) -> str:
    """Send a prompt to the chosen AI provider and return the response text."""
    provider = provider.lower()

    if provider == "openai":
        return _call_openai(api_key, model, prompt)
    elif provider == "claude":
        return _call_claude(api_key, model, prompt)
    elif provider == "grok":
        return _call_grok(api_key, model, prompt)
    elif provider == "gemini":
        return _call_gemini(api_key, model, prompt)
    else:
        sys.exit(f"Error: Unknown provider '{provider}'. Supported: {', '.join(PROVIDERS.keys())}")


def _call_openai(api_key: str, model: str, prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert agent designer. Respond ONLY with the requested Markdown content. Do not wrap the output in code fences."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _call_claude(api_key: str, model: str, prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system="You are an expert agent designer. Respond ONLY with the requested Markdown content. Do not wrap the output in code fences.",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.content[0].text.strip()


def _call_grok(api_key: str, model: str, prompt: str) -> str:
    # Grok uses the OpenAI-compatible API via xAI
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert agent designer. Respond ONLY with the requested Markdown content. Do not wrap the output in code fences."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _call_gemini(api_key: str, model: str, prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=(
            "You are an expert agent designer. Respond ONLY with the requested Markdown content. "
            "Do not wrap the output in code fences.\n\n" + prompt
        ),
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# Prompt template loader
# ---------------------------------------------------------------------------

# Directory where prompt .txt templates live (next to this script)
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(template_name: str, **kwargs: str) -> str:
    """Load a prompt template from the prompts/ folder and substitute placeholders.

    Templates use ``string.Template`` syntax — ``${variable}`` placeholders are
    replaced with the corresponding keyword argument values.
    """
    template_path = PROMPTS_DIR / template_name
    if not template_path.exists():
        sys.exit(f"Error: Prompt template not found: {template_path}")
    raw = template_path.read_text(encoding="utf-8")
    return Template(raw).substitute(**kwargs)


# ---------------------------------------------------------------------------
# Interactive input helpers
# ---------------------------------------------------------------------------

def prompt_input(label: str, current: str | None = None) -> str:
    """Prompt the user for input, showing a current/default value if available."""
    if current:
        value = input(f"{label} [{current}]: ").strip()
        return value if value else current
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  (This field is required.)")


def prompt_choice(label: str, choices: list[str], current: str | None = None) -> str:
    """Prompt the user to pick from a list of choices."""
    print(f"\n{label}")
    for i, c in enumerate(choices, 1):
        marker = " *" if current and c.lower() == current.lower() else ""
        print(f"  {i}. {c}{marker}")
    while True:
        raw = input("Enter number or name: ").strip()
        if not raw and current:
            return current
        # Try numeric
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        # Try name match
        for c in choices:
            if raw.lower() == c.lower():
                return c
        print("  Invalid choice. Try again.")


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_configure(args: argparse.Namespace) -> None:
    """Interactive configuration wizard."""
    cfg = load_config()

    print("\n=== SoulClaw Configuration ===\n")

    provider_names = [PROVIDERS[k]["label"] for k in PROVIDERS]
    provider_keys = list(PROVIDERS.keys())

    # Resolve current provider label for display
    current_provider_label = None
    if "provider" in cfg:
        current_provider_label = PROVIDERS.get(cfg["provider"], {}).get("label")

    chosen_label = prompt_choice(
        "Select AI provider:",
        provider_names,
        current=current_provider_label,
    )
    # Map label back to key
    chosen_key = provider_keys[provider_names.index(chosen_label)]
    cfg["provider"] = chosen_key

    default_model = PROVIDERS[chosen_key]["default_model"]
    current_model = cfg.get("model", default_model)
    cfg["model"] = prompt_input(f"Model name (default: {default_model})", current=current_model)

    cfg["api_key"] = prompt_input("API key", current=cfg.get("api_key"))

    save_config(cfg)
    print("\nDone! You can now run `soulclaw generate` to create agent files.\n")


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate the four Openclaw Markdown files."""
    cfg = load_config()

    # --- Resolve provider / model / key (CLI flags override config) ----------
    provider = (args.provider or cfg.get("provider", "")).lower()
    model = args.model or cfg.get("model", "")
    api_key = args.api_key or cfg.get("api_key", "")

    if not provider:
        sys.exit(
            "Error: No AI provider configured. Run `soulclaw configure` first "
            "or pass --provider."
        )
    if provider not in PROVIDERS:
        sys.exit(f"Error: Unknown provider '{provider}'. Supported: {', '.join(PROVIDERS.keys())}")
    if not model:
        model = PROVIDERS[provider]["default_model"]
    if not api_key:
        sys.exit(
            "Error: No API key configured. Run `soulclaw configure` first "
            "or pass --api-key."
        )

    # --- Gather agent info (CLI flags or interactive) ------------------------
    who = args.who or ""
    objective = args.objective or ""
    audience = args.audience or ""
    location = args.location or ""

    if not who:
        who = prompt_input("Who does the agent represent? (name & what it does)")
    if not objective:
        objective = prompt_input("What is the agent going to do?")
    if not audience:
        audience = prompt_input("Describe the target audience")
    if not location:
        location = prompt_input("Where is the target audience located? (include region)")

    # --- Output directory ----------------------------------------------------
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Generate files ------------------------------------------------------
    # Each entry maps an output filename to its prompt template file
    files_to_generate = [
        ("SOUL.md",     "soul.txt"),
        ("IDENTITY.md", "identity.txt"),
        ("GOALS.md",    "goals.txt"),
        ("USER.md",     "user.txt"),
    ]

    replacements = {
        "who": who,
        "objective": objective,
        "audience": audience,
        "location": location,
    }

    print(f"\nUsing provider: {PROVIDERS[provider]['label']}  |  model: {model}")
    print(f"Output directory: {output_dir}\n")

    for filename, template_name in files_to_generate:
        print(f"Generating {filename} ... ", end="", flush=True)
        prompt = load_prompt(template_name, **replacements)
        try:
            content = call_ai(provider, model, api_key, prompt)
        except Exception as e:
            print(f"FAILED\n  Error: {e}")
            continue
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"OK  -> {filepath}")

    print("\nAll files generated successfully!")


def cmd_show_config(args: argparse.Namespace) -> None:
    """Display the current configuration."""
    cfg = load_config()
    if not cfg:
        print("No configuration found. Run `soulclaw configure` to set one up.")
        return
    print("\n=== Current Configuration ===\n")
    print(f"  Provider : {PROVIDERS.get(cfg.get('provider', ''), {}).get('label', cfg.get('provider', 'N/A'))}")
    print(f"  Model    : {cfg.get('model', 'N/A')}")
    key = cfg.get("api_key", "")
    masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
    print(f"  API Key  : {masked}")
    print(f"  File     : {_config_file()}\n")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="soulclaw",
        description="SoulClaw CLI — Generate Openclaw-compatible agent definition files using AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              soulclaw configure                Set up AI provider and API key
              soulclaw show-config              Display current configuration
              soulclaw generate                 Interactive generation
              soulclaw generate --who "Acme Corp, a SaaS company" \\
                  --objective "Answer customer support calls" \\
                  --audience "Small business owners" \\
                  --location "California, USA" \\
                  --output-dir ./agent
        """),
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- configure -----------------------------------------------------------
    subparsers.add_parser(
        "configure",
        help="Interactively configure the AI provider, model, and API key",
    )

    # --- show-config ---------------------------------------------------------
    subparsers.add_parser(
        "show-config",
        help="Display the current stored configuration",
    )

    # --- generate ------------------------------------------------------------
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate the four Openclaw Markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gen_parser.add_argument(
        "--who",
        type=str,
        default=None,
        help="Who the agent represents (name of business/person and what it does)",
    )
    gen_parser.add_argument(
        "--objective",
        type=str,
        default=None,
        help="What this agent is going to do (e.g. answer calls for my business)",
    )
    gen_parser.add_argument(
        "--audience",
        type=str,
        default=None,
        help="Describe the target audience (e.g. university professors, firefighters)",
    )
    gen_parser.add_argument(
        "--location",
        type=str,
        default=None,
        help="Where the target audience is located, including region (e.g. Maryland, USA)",
    )
    gen_parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=".",
        help="Directory to write generated files to (default: current directory)",
    )
    gen_parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=list(PROVIDERS.keys()),
        help="Override the configured AI provider",
    )
    gen_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override the configured model name",
    )
    gen_parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Override the configured API key",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "configure": cmd_configure,
        "show-config": cmd_show_config,
        "generate": cmd_generate,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
