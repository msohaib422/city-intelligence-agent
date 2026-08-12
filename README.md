# 🌆 City Intelligence System

An AI agent that answers natural-language questions about a city's **current weather** and **latest news**, built with **LangChain**, **Mistral AI**, and a **Streamlit** front end.

The agent autonomously decides which tool to call (weather API, news search, or none), executes it, and reasons over the result to produce a final natural-language answer — a minimal, production-style example of **tool-calling / function-calling agent architecture**.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [How the Agent Works](#how-the-agent-works)
- [Configuration](#configuration)
- [Deployment](#deployment)
  - [Streamlit Community Cloud](#streamlit-community-cloud)
  - [Docker](#docker)
- [Security Considerations](#security-considerations)
- [Cost & Rate Limits](#cost--rate-limits)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Limitations & Known Issues](#limitations--known-issues)
- [Roadmap](#roadmap)
- [Troubleshooting / FAQ](#troubleshooting--faq)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

City Intelligence System is a chat-based agent that can:

- Look up **real-time weather** for any city (OpenWeatherMap API)
- Search for **recent news** about any city (Tavily Search API)
- Decide **on its own** whether a tool is needed, which one, and with what arguments — powered by Mistral's function-calling capability via LangChain

The project demonstrates a clean, minimal **ReAct-style tool-calling loop**: the LLM is invoked, it either returns a final answer or requests one or more tool calls, the tools are executed, and their results are fed back into the conversation until the model produces a final response.

---

## Features

| Feature | Description |
|---|---|
| 🌤️ Weather lookup | Live temperature and conditions via OpenWeatherMap |
| 📰 News search | Latest headlines for a city via Tavily |
| 🤖 Autonomous tool routing | The LLM decides when/which tool to call — no hardcoded intent matching |
| 💬 Conversational memory | Full chat history is preserved and sent with every request |
| 🎨 Responsive UI | Custom Streamlit theme, mobile-friendly layout, collapsible sidebar |
| 🔐 Environment-based secrets | All API keys loaded from `.env`, never hardcoded |
| 🧩 Extensible tool interface | New tools can be added by writing a function and registering it |

---

## Architecture

```
┌──────────────┐        ┌──────────────────┐        ┌───────────────────┐
│   Streamlit   │  msgs  │   LangChain Chat  │  calls │   Tool Functions   │
│   Chat UI     │ ─────► │   Model (Mistral) │ ─────► │  get_weather /     │
│  (app.py)     │ ◄───── │  + bind_tools()   │ ◄───── │  get_news          │
└──────────────┘ result └──────────────────┘ result └───────────────────┘
                                                              │
                                              ┌───────────────┴───────────────┐
                                              │                               │
                                     ┌────────▼────────┐           ┌─────────▼─────────┐
                                     │ OpenWeatherMap   │           │  Tavily Search API │
                                     │      API         │           │                    │
                                     └──────────────────┘           └────────────────────┘
```

**Request lifecycle (per user message):**

1. User message is appended to the conversation as a `HumanMessage`.
2. The full message history is sent to the Mistral model via `llm.bind_tools([...])`.
3. The model responds with either:
   - **Final content** → shown directly to the user, loop ends, or
   - **One or more `tool_calls`** → each is executed, its result wrapped in a `ToolMessage`, and appended back to history.
4. The loop repeats from step 2 until the model returns a final answer with no further tool calls.

This mirrors how production agent frameworks (LangGraph, OpenAI Assistants, AutoGen) structure their control loop, just implemented explicitly for transparency.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | [Mistral AI](https://mistral.ai/) (`mistral-small-2506`) via `langchain-mistralai` |
| Agent framework | [LangChain](https://python.langchain.com/) tool-calling (`bind_tools`) |
| Web search tool | [Tavily Search API](https://tavily.com/) via `langchain-tavily` |
| Weather data | [OpenWeatherMap API](https://openweathermap.org/api) |
| Frontend | [Streamlit](https://streamlit.io/) |
| Config management | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| Language | Python 3.10+ |

---

## Project Structure

```
city-intelligence-system/
├── app.py               # Streamlit app: UI, session state, agent loop, tools
├── requirements.txt      # Python dependencies
├── .env.example           # Template for required environment variables
├── .env                   # Your local secrets (NOT committed to git)
├── .gitignore
└── README.md
```

---

## Prerequisites

- Python **3.10 or higher**
- API keys for:
  - **Mistral AI** — [console.mistral.ai](https://console.mistral.ai/)
  - **OpenWeatherMap** — [openweathermap.org/api](https://openweathermap.org/api)
  - **Tavily** — [tavily.com](https://tavily.com/)
- `pip` and a virtual environment tool (`venv`, `conda`, or `poetry`)

---

## Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/city-intelligence-system.git
cd city-intelligence-system

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then open .env and paste in your real API keys
```

---

## Environment Variables

Create a `.env` file in the project root (see `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `MISTRAL_API_KEY` | ✅ | Auth key for the Mistral chat model |
| `OPENWEATHER_API_KEY` | ✅ | Auth key for OpenWeatherMap current-weather endpoint |
| `TAVILY_API_KEY` | ✅ | Auth key for Tavily news/web search |

> **Never commit `.env` to version control.** It is already excluded via `.gitignore`. In production, inject these as platform secrets (see [Deployment](#deployment)) rather than shipping a `.env` file.

---

## Running the App

```bash
streamlit run app.py
```

By default Streamlit serves the app at `http://localhost:8501`. Open that URL in your browser (or on your phone, on the same network, via your machine's local IP) to use the chat interface.

---

## How the Agent Works

The core loop lives in `run_agent_turn()` inside `app.py`:

```python
def run_agent_turn():
    while True:
        result = llm_with_tool.invoke(st.session_state.messages)
        st.session_state.messages.append(result)

        if result.tool_calls:
            for tool_call in result.tool_calls:
                tool_result = tools[tool_call["name"]].invoke(tool_call["args"])
                st.session_state.messages.append(
                    ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
                )
            continue
        else:
            # Final answer — display and stop
            break
```

- `llm.bind_tools([get_weather, get_news])` exposes the tool **name, description (docstring), and argument schema** to the model, letting Mistral decide autonomously whether/which to invoke.
- Tool calls are executed **synchronously and automatically** (no manual approval step) — the agent runs end-to-end per user turn.
- Every `ToolMessage` is linked back to its originating call via `tool_call_id`, which is required by the OpenAI/Mistral function-calling message format.

### Adding a new tool

1. Write a plain Python function with a clear docstring (this becomes the tool description the LLM sees):
   ```python
   @tool
   def get_currency_rate(base: str, target: str) -> str:
       """Get the exchange rate between two currencies."""
       ...
   ```
2. Register it in `bind_tools([...])` and the `tools` dict.
3. Optionally add a friendly label to `TOOL_LABELS` for the UI badge.

---

## Configuration

| Setting | Where | Notes |
|---|---|---|
| Model name | `ChatMistralAI(model="mistral-small-2506")` in `app.py` | Swap for any Mistral model that supports tool calling |
| Max search results | `TavilySearch(max_results=2, ...)` | Increase for broader news coverage (higher latency/cost) |
| Sidebar default state | `initial_sidebar_state="collapsed"` | Set to `"expanded"` for desktop-first deployments |

---

## Deployment

### Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/) → **New app** → select the repo and `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   MISTRAL_API_KEY = "..."
   OPENWEATHER_API_KEY = "..."
   TAVILY_API_KEY = "..."
   ```
4. Deploy. Streamlit Cloud injects secrets as environment variables automatically, so no code changes are needed.

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t city-intelligence-system .
docker run -p 8501:8501 --env-file .env city-intelligence-system
```

For cloud hosting (Render, Railway, AWS ECS/Fargate, GCP Cloud Run, Azure Container Apps), pass the three API keys as platform-managed environment variables/secrets rather than baking them into the image.

---

## Security Considerations

- **Secrets management:** API keys are read only from environment variables (`os.getenv`). Never hardcode keys in source. In CI/CD, use your platform's secret store (GitHub Actions Secrets, AWS Secrets Manager, etc.).
- **Third-party API exposure:** Both external tools call third-party services directly from the server process — the frontend never receives raw API keys.
- **Input handling:** City names are passed as free-text arguments to external APIs; both integrations already return structured error messages instead of raw stack traces on failure.
- **No persistent storage:** Conversation state lives only in Streamlit's in-memory session state and is cleared when the session ends or the user clicks "Clear conversation." Nothing is written to disk or a database.
- **Dependency hygiene:** Pin dependency versions in `requirements.txt` for production and run `pip-audit` / `safety` periodically to catch known CVEs.
- **Rate limiting:** Currently none is enforced at the app layer — for public deployments, add per-session or per-IP rate limiting to avoid API quota exhaustion or abuse.

---

## Cost & Rate Limits

| Service | Free tier (approx., verify current terms) | Notes |
|---|---|---|
| Mistral AI | Pay-per-token, no perpetual free tier | Cost scales with conversation length; trim history for long sessions |
| OpenWeatherMap | ~1,000 calls/day on free tier | One call per weather query |
| Tavily | Limited free credits/month | One call per news query |

Always check each provider's current pricing page before production use — free-tier limits change over time.

---

## Error Handling

- **Missing API key:** Each tool returns a descriptive `"Error: ... not found"` string instead of raising, so the agent can gracefully explain the failure to the user rather than crashing.
- **Invalid city / API failure:** `get_weather` surfaces the upstream error message (`data.get("message")`) directly to the model, which can relay it conversationally.
- **Empty search results:** `get_news` returns `"No news found."` instead of an empty/ambiguous response.
- **LLM/network failures:** Not currently caught explicitly — for production, wrap `llm_with_tool.invoke(...)` in a `try/except` and surface a user-friendly fallback message plus structured logging (see [Roadmap](#roadmap)).

---

## Testing

This starter project does not yet ship automated tests. Recommended additions for a production-grade setup:

```
tests/
├── test_tools.py        # Unit tests for get_weather / get_news with mocked HTTP calls
├── test_agent_loop.py    # Tests for the tool-calling loop logic with a stubbed LLM
└── conftest.py            # Shared fixtures (mock env vars, mock responses)
```

- Mock `requests.get` and `TavilySearch.invoke` with `unittest.mock` or `responses` to avoid live API calls in CI.
- Use `pytest` + `pytest-cov` and wire into GitHub Actions for CI on every PR.

---

## Limitations & Known Issues

- Weather and news tools only accept a single free-text `city` string — no disambiguation for cities sharing a name across countries (e.g., "Springfield").
- No streaming responses — the full model reply is awaited before rendering.
- No persistent chat history across browser sessions/devices.
- No authentication — anyone with the URL can use the app and consume your API quota if deployed publicly without additional access control.

---

## Roadmap

- [ ] Add automated test suite (unit + integration)
- [ ] Add structured logging and request tracing
- [ ] Add streaming token-by-token responses
- [ ] Add rate limiting / usage quotas per session
- [ ] Add optional authentication (e.g., Streamlit `st.secrets` + simple login, or OAuth)
- [ ] Support multi-turn city disambiguation (country/state selection)
- [ ] Add caching layer for repeated weather/news queries (e.g., short-TTL cache)
- [ ] CI/CD pipeline (lint, test, deploy on merge)

---

## Troubleshooting / FAQ

**The app starts but every tool call fails with "key not found."**
Check that `.env` exists in the project root and all three variables are set, then restart the Streamlit process (env vars are read at startup / cache time via `@st.cache_resource`).

**Weather works but news doesn't (or vice versa).**
Verify the specific provider's key independently — the sidebar status pills show which service is missing a key.

**Changes to `app.py` aren't reflected.**
Streamlit auto-reloads on file save by default; if it doesn't, use the "Rerun" option in the top-right menu or restart the server. If you changed `@st.cache_resource`-wrapped code (`load_llm`), a full restart may be required to clear the cache.

**Sidebar arrow not visible on mobile.**
Ensure you're on the latest Streamlit version — internal `data-testid` attributes for the sidebar toggle can change between releases, which may require updating the CSS selectors in `app.py`.

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feature/my-feature`
2. Follow existing code style (PEP 8, type hints where practical)
3. Add/update tests for any behavior change
4. Open a pull request with a clear description of the change and rationale

---

## License

This project is provided under the **MIT License**. See `LICENSE` for details (add one if not already present).

---

## Acknowledgements

- [LangChain](https://python.langchain.com/) for the agent/tool-calling framework
- [Mistral AI](https://mistral.ai/) for the underlying LLM
- [Tavily](https://tavily.com/) for search API access
- [OpenWeatherMap](https://openweathermap.org/) for weather data
- [Streamlit](https://streamlit.io/) for the rapid UI framework
