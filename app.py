import os
import requests
import streamlit as st
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
from langchain_mistralai import ChatMistralAI
from langchain.messages import HumanMessage, ToolMessage

load_dotenv()

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="City Intelligence System",
    page_icon="🌆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CUSTOM CSS — PROFESSIONAL & MOBILE RESPONSIVE
# =========================================================
st.markdown(
    """
    <style>
        #MainMenu, footer {visibility: hidden;}

        /* Keep the header bar — it holds the sidebar open/close arrow */
        header[data-testid="stHeader"] {
            background: transparent;
        }

        .stApp {
            background: radial-gradient(circle at top, #131722 0%, #0b0e14 60%);
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 6rem;
            max-width: 780px;
        }

        /* -------- Sidebar open/close arrow: always visible, styled as a round icon button -------- */
        [data-testid="collapsedControl"],
        button[data-testid="stSidebarCollapseButton"],
        button[data-testid="baseButton-headerNoPadding"] {
            visibility: visible !important;
            display: flex !important;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1f6feb 0%, #6e40c9 100%) !important;
            border-radius: 50% !important;
            width: 2.3rem !important;
            height: 2.3rem !important;
            box-shadow: 0 4px 14px rgba(31, 111, 235, 0.35);
        }
        [data-testid="collapsedControl"] svg,
        button[data-testid="stSidebarCollapseButton"] svg,
        button[data-testid="baseButton-headerNoPadding"] svg {
            fill: #ffffff !important;
            color: #ffffff !important;
        }

        @media (max-width: 640px) {
            [data-testid="collapsedControl"],
            button[data-testid="stSidebarCollapseButton"],
            button[data-testid="baseButton-headerNoPadding"] {
                width: 2.5rem !important;
                height: 2.5rem !important;
                position: fixed !important;
                top: 0.6rem !important;
                left: 0.6rem !important;
                z-index: 999999 !important;
            }
        }

        .app-header {
            padding: 1.4rem 1.6rem;
            border-radius: 16px;
            background: linear-gradient(135deg, #1f6feb 0%, #6e40c9 100%);
            margin-bottom: 1.2rem;
            box-shadow: 0 10px 30px rgba(31, 111, 235, 0.25);
        }
        .app-header h1 {
            color: #ffffff;
            font-size: 1.5rem;
            margin: 0;
            font-weight: 700;
            line-height: 1.3;
        }
        .app-header p {
            color: rgba(255,255,255,0.85);
            margin: 0.3rem 0 0 0;
            font-size: 0.9rem;
        }

        section[data-testid="stChatMessage"] {
            border-radius: 14px;
            padding: 0.35rem 0.1rem;
        }

        div[data-testid="stChatMessageContent"] {
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .tool-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: rgba(111, 211, 255, 0.1);
            border: 1px solid rgba(111, 211, 255, 0.25);
            color: #6fd3ff;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            margin-bottom: 0.5rem;
        }

        div[data-testid="stChatInput"] textarea {
            border-radius: 12px !important;
        }

        [data-testid="stSidebar"] {
            background: #10131c;
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        .status-pill {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .pill-ok  { background: rgba(46, 204, 113, 0.15); color: #2ecc71; }
        .pill-bad { background: rgba(231, 76, 60, 0.15);  color: #e74c3c; }

        /* ---------- Mobile responsiveness ---------- */
        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.8rem;
                padding-right: 0.8rem;
                padding-top: 3.4rem;
            }
            .app-header {
                padding: 1.1rem 1.1rem;
                border-radius: 12px;
            }
            .app-header h1 {
                font-size: 1.2rem;
            }
            .app-header p {
                font-size: 0.82rem;
            }
            div[data-testid="stChatMessageContent"] {
                font-size: 0.9rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TOOLS (logic unchanged from the original script)
# =========================================================
@tool
def get_weather(city: str) -> str:
    """Get the current weather of a city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY not found."
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("cod") != 200:
        return f"Error: {data.get('message')}"
    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    return f"Weather in {city}: {desc}, {temp}°C"


tavily_client = TavilySearch(max_results=2, topic="news")


@tool
def get_news(city: str) -> str:
    """Get the latest news about a city."""
    query = f"latest news in {city}"
    results = tavily_client.invoke({"query": query})
    if not results:
        return "No news found."
    news = []
    for result in results["results"]:
        title = result["title"]
        url = result["url"]
        news.append(f"{title}\n{url}")
    return "\n\n".join(news)


@st.cache_resource(show_spinner=False)
def load_llm():
    base_llm = ChatMistralAI(model="mistral-small-2506")
    return base_llm.bind_tools([get_weather, get_news])


llm_with_tool = load_llm()
tools = {"get_weather": get_weather, "get_news": get_news}

TOOL_LABELS = {
    "get_weather": "🌤️ Checking the weather",
    "get_news": "📰 Fetching the latest news",
}

# =========================================================
# SESSION STATE
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []  # LangChain messages sent to the model
if "display_log" not in st.session_state:
    st.session_state.display_log = []  # Chat bubbles shown to the user

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### 🌆 City Intelligence")
    st.caption("An AI agent for weather & city news")
    st.divider()
    st.markdown("**Connections**")

    def pill(ok: bool) -> str:
        return (
            '<span class="status-pill pill-ok">Connected</span>'
            if ok
            else '<span class="status-pill pill-bad">Missing key</span>'
        )

    st.markdown(
        f"Mistral &nbsp; {pill(bool(os.getenv('MISTRAL_API_KEY')))}",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"OpenWeather &nbsp; {pill(bool(os.getenv('OPENWEATHER_API_KEY')))}",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Tavily &nbsp; {pill(bool(os.getenv('TAVILY_API_KEY')))}",
        unsafe_allow_html=True,
    )

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.display_log = []
        st.rerun()

# =========================================================
# HEADER
# =========================================================
st.markdown(
    """
    <div class="app-header">
        <h1>🌆 City Intelligence System</h1>
        <p>Ask about the weather or the latest news in any city — answered instantly.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# RENDER CHAT HISTORY
# =========================================================
for entry in st.session_state.display_log:
    role = entry["role"]
    avatar = "🧑" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        if entry.get("badge"):
            st.markdown(
                f'<span class="tool-badge">{entry["badge"]}</span>',
                unsafe_allow_html=True,
            )
        st.markdown(entry["content"])


# =========================================================
# AGENT TURN — RUNS THE FULL TOOL-CALLING LOOP AUTOMATICALLY
# =========================================================
def run_agent_turn():
    while True:
        result = llm_with_tool.invoke(st.session_state.messages)
        st.session_state.messages.append(result)

        if result.tool_calls:
            for tool_call in result.tool_calls:
                tool_name = tool_call["name"]
                with st.spinner(TOOL_LABELS.get(tool_name, f"Running {tool_name}...")):
                    tool_result = tools[tool_name].invoke(tool_call["args"])
                st.session_state.messages.append(
                    ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
                )
                st.session_state.display_log.append(
                    {
                        "role": "assistant",
                        "badge": TOOL_LABELS.get(tool_name, tool_name),
                        "content": tool_result,
                    }
                )
            continue
        else:
            st.session_state.display_log.append(
                {"role": "assistant", "content": result.content}
            )
            break


# =========================================================
# CHAT INPUT
# =========================================================
user_input = st.chat_input("Ask about weather or news in a city...")
if user_input:
    st.session_state.messages.append(HumanMessage(content=user_input))
    st.session_state.display_log.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            run_agent_turn()
    st.rerun()
