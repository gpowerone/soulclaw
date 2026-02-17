# SoulClaw CLI

A cross-platform Python CLI that generates [Openclaw](https://openclaw.ai)-compatible agent definition files using AI. It collects information about your agent — who it represents, what it does, who its audience is, and where they are — then generates four structured Markdown files (`SOUL.md`, `IDENTITY.md`, `GOALS.md`, `USER.md`) via the AI provider of your choice.

## Supported AI Providers

| Provider | API Type | Default Model |
|----------|----------|---------------|
| OpenAI   | `openai` | `gpt-4o` |
| Anthropic Claude | `claude` | `claude-sonnet-4-20250514` |
| xAI Grok | `grok` | `grok-3` |
| Google Gemini | `gemini` | `gemini-2.0-flash` |

## Requirements

- **Python 3.10+**
- An API key for one of the supported providers

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-org/soulclaw.git
cd soulclaw
```

### 2. Create a virtual environment (recommended)

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** You only need the SDK for the provider you intend to use. For example, if you only use OpenAI you can run `pip install openai` instead of installing all dependencies.

## Quick Start

### Step 1 — Configure your AI provider

Run the interactive configuration wizard:

```bash
python soulclaw_cli.py configure
```

You will be prompted to select a provider, model, and enter your API key. The configuration is stored per-user on your machine:

| OS      | Config location |
|---------|-----------------|
| macOS   | `~/Library/Application Support/soulclaw/config.json` |
| Linux   | `~/.config/soulclaw/config.json` |
| Windows | `%APPDATA%\soulclaw\config.json` |

### Step 2 — Generate agent files

Run interactively (you'll be prompted for each input):

```bash
python soulclaw_cli.py generate
```

Or pass everything via flags:

```bash
python soulclaw_cli.py generate \
  --who "Acme Corp, a B2B SaaS company providing HR tools" \
  --objective "Answer inbound customer support calls and resolve tier-1 issues" \
  --audience "HR managers at mid-size companies" \
  --location "East Coast, USA" \
  --output-dir ./my-agent
```

The four generated files will be written to the specified output directory (defaults to the current directory).

## Usage Reference

```
soulclaw_cli.py [-h] {configure,show-config,generate} ...
```

### Commands

| Command | Description |
|---------|-------------|
| `configure` | Interactively set up the AI provider, model, and API key |
| `show-config` | Display the current stored configuration (API key is masked) |
| `generate` | Generate the four Openclaw Markdown files |

### `generate` Options

| Flag | Description |
|------|-------------|
| `--who` | Who the agent represents (business/person name & what it does) |
| `--objective` | What the agent is going to do |
| `--audience` | Target audience description |
| `--location` | Target audience location including region |
| `-o`, `--output-dir` | Directory to write files to (default: `.`) |
| `--provider` | Override the configured AI provider (`openai`, `claude`, `grok`, `gemini`) |
| `--model` | Override the configured model name |
| `--api-key` | Override the configured API key |

Any flag not supplied will be prompted interactively (for the four agent questions) or pulled from saved configuration (for provider/model/key).

### Help

```bash
python soulclaw_cli.py -h
python soulclaw_cli.py generate -h
```

## Generated Files

| File | Purpose |
|------|---------|
| `SOUL.md` | Agent personality — interaction style, tone, pacing, and emotional register tailored to the target audience and location |
| `IDENTITY.md` | Agent appearance — name, pronouns, nicknames, physical appearance, voice tone/accent, and defining characteristics |
| `GOALS.md` | Finite actionable steps to accomplish the agent's objective |
| `USER.md` | Profile of the people the agent is trying to help |

## Prompt Templates

The prompts sent to the AI are stored as plain-text template files in the `prompts/` directory:

| Template file | Generates |
|---------------|-----------|
| `prompts/soul.txt` | `SOUL.md` — agent personality |
| `prompts/identity.txt` | `IDENTITY.md` — agent appearance |
| `prompts/goals.txt` | `GOALS.md` — agent objectives |
| `prompts/user.txt` | `USER.md` — target user profile |

Templates use `${variable}` placeholders (Python `string.Template` syntax) that are replaced at runtime with the values you provide. The available placeholders are:

| Placeholder | Source |
|-------------|--------|
| `${who}` | `--who` flag / interactive prompt |
| `${objective}` | `--objective` flag / interactive prompt |
| `${audience}` | `--audience` flag / interactive prompt |
| `${location}` | `--location` flag / interactive prompt |

You can freely edit the template files to customise the prompts — add instructions, change tone guidance, restructure sections, etc. — without touching the Python code.

## Cross-Platform Compatibility

SoulClaw CLI runs on **macOS**, **Linux**, and **Windows**. Configuration is stored using platform-appropriate directories (`XDG_CONFIG_HOME` on Linux, `Application Support` on macOS, `APPDATA` on Windows).

## License

MIT — see [LICENSE](LICENSE) for details.
