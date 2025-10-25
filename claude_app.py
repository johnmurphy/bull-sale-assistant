# Add a comment at the TOP of claude_app.py
# Line 2, add: # Updated branding - [current date/time]

# ============================================================
# 📘 CLOSE ENOUGH CATTLE CO. — CLAUDE SONNET 4.5 BULL SALE ASSISTANT
# ------------------------------------------------------------
# Streamlit application using Claude Sonnet 4.5 tool-calling on your
# Angus bull sale CSV (EPD + ACC + demographics). Provides grounded,
# repeatable recommendations and comparisons without pasting the CSV
# into the prompt (keeps tokens small & performance tight).
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from typing import List, Dict, Any
from anthropic import Anthropic
from datetime import datetime

# ============================================================
# 🧱 PAGE CONFIGURATION & GLOBAL STYLING (ORIGINAL CSS RESTORED)
# ============================================================
st.set_page_config(
    page_title="Close Enough Cattle Co. Bull Sale Assistant",
    page_icon="icon.png",
    layout="centered",
)

# ============================================================
# 🎨 GLOBAL STYLING - LOAD FIRST
# ============================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Lato:wght@400;600&display=swap');
html,body,[class*="css"]{background-color:#faf8f3;color:#3a2f21;font-family:'Lato',sans-serif!important;}
h1,h2,h3{font-family:'Merriweather',serif!important;color:#2d1f10!important;}
h1{font-size:2.5rem!important;font-weight:700!important;margin-bottom:.25rem!important;}
h2{font-size:1.75rem!important;font-weight:700!important;margin:2rem 0 1rem!important;}
h3{font-size:1.4rem!important;font-weight:700!important;margin-bottom:.5rem!important;}
.main>div:first-child [data-testid="stHorizontalBlock"]{
 background:linear-gradient(135deg,#f5f1e8 0%,#ede7db 100%);
 border:2px solid #c7b299;border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;
 box-shadow:0 2px 8px rgba(61,47,33,.08);}
.company-name{font-family:'Merriweather',serif;font-size:2rem;font-weight:700;color:#2d1f10;}
.subtitle{font-family:'Lato',sans-serif;font-size:1.3rem;color:#6b5d4f;font-style:italic;}
.assistant-bubble{background:#fff;border:1px solid #d4c4b0;border-left:4px solid #8b7355;
 border-radius:8px;padding:1.2rem 1.4rem;margin-bottom:1.2rem;color:#3a2f21;
 line-height:1.5;font-size:1rem;box-shadow:0 1px 4px rgba(0,0,0,.06);}
.assistant-bubble b{color:#2d1f10;font-weight:600;display:inline-block;}
.assistant-bubble p{margin:0!important;padding:0!important;}
.assistant-bubble hr{margin:1rem 0;border:0;border-top:1px solid #d4c4b0;}
.user-bubble{background:#e8dfc8;border:1px solid #c7b299;border-radius:8px;
 padding:1rem 1.4rem;margin-bottom:1.2rem;color:#2d1f10;line-height:1.6;font-size:1rem;
 font-weight:500;box-shadow:0 1px 3px rgba(0,0,0,.08);}
.stChatInputContainer{border-top:2px solid #e0d5c3!important;padding-top:1.5rem!important;margin-top:1.5rem!important;}
.welcome-intro{font-size:1.05rem;line-height:1.8;margin-bottom:1.2rem;}
.example-questions{font-size:1.05rem;line-height:1.5;}
.example-questions ul{margin-left:1rem!important;margin-bottom:0!important;padding-left:1.2rem!important;}
.example-questions li{margin-bottom:.2rem!important;line-height:1.4!important;padding-bottom:0!important;margin-top:0!important;}
.example-questions ul li{margin-bottom:.2rem!important;padding:0!important;}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# 🔒 PASSWORD PROTECTION
# ============================================================
# Initialize authentication state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Show password screen if not authenticated
if not st.session_state.authenticated:
    # Header with logo and branding
    col1, col2 = st.columns([1, 3])
    with col1:
        try:
            st.image("logo.png", width=180)
        except Exception:
            pass
    with col2:
        st.markdown(
            """
    <div style='padding-top:18px;'>
      <div class='company-name'>Fall 2025 Angus Bull Sale</div>
      <div class='subtitle'>Bull Sale Assistant - Testing Access</div>
    </div>
    """,
            unsafe_allow_html=True,
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Password input with custom label styling
    st.markdown(
        "<div style='font-family:\"Lato\",sans-serif;font-size:1.05rem;font-weight:500;color:#3a2f21;margin-bottom:0.5rem;'>Enter access code:</div>",
        unsafe_allow_html=True
    )
    password = st.text_input("Enter access code:", type="password", key="password_input", label_visibility="collapsed")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Submit", key="submit_password"):
            # Password stored securely in Streamlit Secrets (not in code)
            correct_password = st.secrets.get("APP_PASSWORD", "")
            if password == correct_password and correct_password != "":
                # Clear everything and start fresh (forces collapsed sidebar)
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.authenticated = True
                st.session_state.query_count = 0
                st.session_state.session_start = datetime.now()
                st.rerun()
            else:
                st.error("❌ Incorrect access code. Please contact Close Enough Cattle Co. for access.")
    
    st.info("🧪 **Testing Phase** - This tool is being evaluated for the 2025 bull sale.")
    st.stop()

# ============================================================
# 🛡️ SESSION RATE LIMITING
# ============================================================
# Initialize session tracking
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now()
    st.session_state.query_count = 0

# Check session limit (50 queries)
if st.session_state.query_count >= 50:
    st.error("⚠️ **Session limit reached** (50 queries). Please refresh the page to continue testing.")
    st.info("This limit helps manage API costs during the testing phase. Thank you for your understanding!")
    if st.button("Refresh Session"):
        # Clear session state to allow reset
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.stop()

def message_bubble(role, content):
    """Uniform chat bubble renderer."""
    cls = "assistant-bubble" if role == "assistant" else "user-bubble"
    
    # Only process content if it's NOT the welcome message (which has proper HTML already)
    if '<div class=' not in content:
        import re
        # Convert markdown bold syntax to HTML: **text** becomes <b>text</b>
        content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
        
        # Convert horizontal rule
        content = content.replace('---', '<hr>')
        
        # Handle newlines:
        # - Double newlines = single blank line (moderate spacing)
        # - Single newlines = line break (tight spacing)
        content = content.replace('\n\n', '<div style="margin-bottom:0.8rem;"></div>')  # Blank line with controlled spacing
        content = content.replace('\n', '<br>')  # Line break
        
        # NOW convert our special placeholder to br (after all other processing)
        content = content.replace('|LINEBREAK|', '<br>')
    
    st.markdown(f"<div class='{cls}'>{content}</div>", unsafe_allow_html=True)

# ============================================================
# 🐂 HEADER
# ============================================================
col1, col2 = st.columns([1, 3])
with col1:
    try:
        st.image("logo.png", width=180)
    except Exception:
        pass
with col2:
    st.markdown(
        """
<div style='padding-top:18px;'>
  <div class='company-name'>Fall 2025 Angus Bull Sale</div>
  <div class='subtitle'>We have 100 young bulls in our catalog.</div>
  <div class='subtitle'>Let's find the bull that best fits your operation.</div>
</div>
""",
        unsafe_allow_html=True,
    )
st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

# ============================================================
# 📊 LOAD & PREPARE SALE DATA
# ============================================================
@st.cache_data
def load_data():
    try:
        return pd.read_csv("augmented_bull_epd_data.csv")
    except FileNotFoundError:
        st.error("📦 File 'augmented_bull_epd_data.csv' not found.")
        st.stop()

bulls: pd.DataFrame = load_data()
bulls_columns = set(bulls.columns.str.strip())
BULL_NAMES_SET = set(bulls["Bull_Name"].str.lower().tolist())

CORE_TRAITS = [
    "CED","BW","WW","YW","Milk","HP","CEM","CW","Marb","RE","Fat",
    "DollarM","DollarB","DollarC","DollarW","DollarEN"
]
ACC_NAMES = set([c for c in bulls_columns if c.startswith("ACC_") or c.endswith("_ACC")])

def get_acc_value(row: pd.Series, trait: str):
    """Return ACC for a trait if present (supports ACC_Trait or Trait_ACC)."""
    for acc_col in (f"ACC_{trait}", f"{trait}_ACC"):
        if acc_col in row.index and pd.notna(row[acc_col]):
            return float(row[acc_col])
    return None

# ============================================================
# 📜 SYSTEM PROMPT & RENDER RULES (SIMPLIFIED - NO REDUNDANCY)
# ============================================================
try:
    with open("instructions.txt") as f:
        system_prompt = f.read()
except FileNotFoundError:
    st.error("⚠️ Missing 'instructions.txt' — include it in the same folder.")
    st.stop()

RENDER_RULES = """
When responding:
- Do NOT say "fetching", "searching", "analyzing", or similar filler.
- Call tools to retrieve data, then show the final, user-ready results.

CRITICAL FORMATTING RULE:
The tool returns a "formatted_block" field. This is a PRE-FORMATTED string with special placeholders.
YOU MUST COPY IT EXACTLY AS-IS. DO NOT:
- Add line breaks or spaces
- Reformat the data
- Split sections onto new lines
- Add colons or punctuation

Just paste the formatted_block string verbatim, then add your analysis after a blank line.

EXACT FORMAT:

[paste formatted_block exactly as received - NO CHANGES]

**Why I recommend:** [brief reasoning]
**Best for:** [production goal]
**Trade-off:** [if applicable, or omit]

---

[next formatted_block - NO CHANGES]

EXAMPLE of correct usage (formatted_block contains special placeholders):

**Pen 1 – NOBLE M070** (See catalog page 1)|LINEBREAK|**Key EPDs:** CED: 11.00, ACC(0.47) | BW: -0.20, ACC(0.50)|LINEBREAK|**Dollar indexes:** DollarM: 76.94, Rank 54

**Why I recommend:** Top carcass value.
**Best for:** Terminal programs.

---

The |LINEBREAK| placeholders will be converted to line breaks automatically. Just paste the string exactly as provided.

"""

# ============================================================
# 🔐 CLAUDE MODEL CONFIG
# ============================================================
api_key = st.secrets.get("ANTHROPIC_API_KEY") or st.secrets.get("CLAUDE_API_KEY")
if not api_key:
    st.error("⚠️ Missing API key: set ANTHROPIC_API_KEY or CLAUDE_API_KEY in .streamlit/secrets.toml")
    st.stop()

client = Anthropic(api_key=api_key)
MODEL_PRIMARY = "claude-sonnet-4-5-20250929"
MODEL_FALLBACK = "claude-3-5-sonnet-20241022"

# ============================================================
# 🧰 TOOL SCHEMA
# ============================================================
TOOLS_SCHEMA = [
    {
        "name": "get_top_bulls",
        "description": (
            "Return the top bulls optimized for a specific breeding goal. "
            "Goals: 'carcass' (DollarC, Marb, CW), 'heifer' (CED, BW), 'maternal' (DollarM, Milk), or 'general' (DollarC, DollarB)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "enum": ["carcass", "heifer", "maternal", "general"],
                    "description": "Breeding objective",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top bulls to return (default 3, max 10)",
                    "default": 3,
                },
            },
            "required": ["goal"],
        },
    },
    {
        "name": "compare_bulls",
        "description": "Compare specific bulls side by side with optional focus on specific traits",
        "input_schema": {
            "type": "object",
            "properties": {
                "bull_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of bull names to compare",
                },
                "focus_traits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: specific traits to focus on (e.g., ['CED', 'BW', 'Milk', 'HP']). If not provided, shows key traits only.",
                },
            },
            "required": ["bull_names"],
        },
    },
    {
        "name": "filter_bulls",
        "description": "Filter bulls by trait value range",
        "input_schema": {
            "type": "object",
            "properties": {
                "trait": {
                    "type": "string",
                    "description": "Trait to filter (e.g., CED, BW, WW, YW, Marb, DollarC)",
                },
                "min_value": {
                    "type": "number",
                    "description": "Minimum value for the trait",
                },
                "max_value": {
                    "type": "number",
                    "description": "Maximum value for the trait",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of results to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["trait"],
        },
    },
]

def pick_goal(user_message: str) -> str:
    """Infer breeding goal from user message."""
    p = user_message.lower()
    if any(k in p for k in ["carcass","marbling","feedlot","terminal","marb","cw","re","fat","dollarc","dollarb"]):
        return "carcass"
    if any(k in p for k in ["heifer","calving","birth","ced","bw"]):
        return "heifer"
    if any(k in p for k in ["maternal","milk","fertility","longevity","cow","replacement","dollarm","dollaren"]):
        return "maternal"
    return "general"

# ============================================================
# 🧩 TOOL IMPLEMENTATIONS - OPTION B (ALL PIPES)
# ============================================================
def build_bull_payload(row: pd.Series, include_traits: List[str]=None) -> Dict[str, Any]:
    """
    Structured bull record with pre-formatted trait strings.
    Returns human-readable strings that Claude can display directly without reformatting.
    
    FORMAT: Both EPDs and Dollar indexes use pipes between items
    - EPDs: "CED: 6.00, ACC(0.50) | BW: -1.40, ACC(0.19)"
    - Dollar indexes: "DollarM: 76.94, Rank 54 | DollarB: 322.89, Rank 100"
    """
    base = {
        "Bull_Name": row["Bull_Name"],
        "Pen": int(row["Pen"]) if pd.notna(row.get("Pen")) else None,
        "Page": int(row["Page"]) if pd.notna(row.get("Page")) else None,
    }
    
    # Separate EPDs and Dollar indexes for clarity
    epds = []
    dollars = []
    
    # Dollar index traits - using "Dollar" prefix instead of "$" to avoid Streamlit LaTeX rendering issues
    dollar_traits = {"DollarM": "DollarM", "DollarB": "DollarB", "DollarC": "DollarC", "DollarW": "DollarW", "DollarEN": "DollarEN"}
    
    traits = include_traits or [t for t in CORE_TRAITS if t in row.index]
    
    for t in traits:
        if t not in row.index or pd.isna(row[t]):
            continue
            
        val = float(row[t])
        
        if t in dollar_traits:
            # Dollar index - format with rank using COMMA before Rank
            rank_col = f"{t}_Rank"
            rank_val = int(row[rank_col]) if rank_col in row.index and pd.notna(row[rank_col]) else None
            
            dollar_name = dollar_traits[t]
            if rank_val is not None:
                dollars.append(f"{dollar_name}: {val:.2f}, Rank {rank_val}")
            else:
                dollars.append(f"{dollar_name}: {val:.2f}")
        else:
            # Regular EPD - format with ACC in parentheses
            acc_val = get_acc_value(row, t)
            if acc_val is not None:
                epds.append(f"{t}: {val:.2f}, ACC({acc_val:.2f})")
            else:
                epds.append(f"{t}: {val:.2f}")
    
    # Build formatted sections with special placeholder for line breaks
    parts = []
    parts.append(f"**Pen {base['Pen']} – {base['Bull_Name']}** (See catalog page {base['Page']})")
    
    if epds:
        parts.append(f"**Key EPDs:** {' | '.join(epds)}")
    
    if dollars:
        parts.append(f"**Dollar indexes:** {' | '.join(dollars)}")
    
    # Use special placeholder that won't get converted during markdown processing
    base["formatted_block"] = "|LINEBREAK|".join(parts)
    
    # Keep individual strings for backward compatibility
    base["epds_formatted"] = " | ".join(epds) if epds else None
    base["dollars_formatted"] = " | ".join(dollars) if dollars else None
    
    return base

def select_sort_for_goal(goal: str):
    """Trait columns + sort order by goal (False = descending is better)."""
    g = goal.lower()
    if g == "carcass":
        cols = [c for c in ["DollarC","DollarB","Marb","CW"] if c in bulls_columns]
        asc  = [False]*len(cols)
    elif g == "heifer":
        cols = [c for c in ["CED","BW","WW","YW"] if c in bulls_columns]
        asc  = [False, True] + [False]*(len(cols)-2)  # BW asc (lower is better)
    elif g == "maternal":
        cols = [c for c in ["DollarM","Milk","HP","CEM"] if c in bulls_columns]
        asc  = [False]*len(cols)
    else:
        cols = [c for c in ["DollarC","DollarB"] if c in bulls_columns]
        asc  = [False]*len(cols)
    return cols, asc

def get_top_bulls_tool(goal: str, top_n: int = 3) -> Dict[str, Any]:
    """Return top bulls for the specified goal (carcass, heifer, maternal, general)."""
    cols, asc = select_sort_for_goal(goal)
    if not cols:
        return {"goal": goal, "bulls": []}
    
    # Define which traits to show based on goal
    g = goal.lower()
    if g == "carcass":
        display_traits = ["CED", "BW", "Marb", "CW", "RE", "DollarC", "DollarB"]
    elif g == "heifer":
        display_traits = ["CED", "BW", "WW", "YW", "DollarB"]
    elif g == "maternal":
        display_traits = ["CED", "BW", "Milk", "HP", "CEM", "DollarM", "DollarEN"]
    else:
        display_traits = ["CED", "BW", "WW", "YW", "Milk", "DollarC", "DollarB"]
    
    df = bulls.dropna(subset=cols, how="all").copy()
    df = df.sort_values(by=cols, ascending=asc).head(top_n)
    return {
        "goal": goal,
        "bulls": [build_bull_payload(row, include_traits=display_traits) for _, row in df.iterrows()]
    }

def compare_bulls_tool(bull_names: List[str], focus_traits: List[str] = None) -> Dict[str, Any]:
    """
    Return side-by-side data for specified bulls.
    If focus_traits is provided, only include those traits in the comparison.
    """
    out = []
    for name in bull_names:
        match = bulls[bulls["Bull_Name"].str.lower() == name.lower()]
        if not match.empty:
            # If focus_traits specified, use only those; otherwise use a sensible default set
            if focus_traits:
                traits_to_include = focus_traits
            else:
                # Default: show key maternal or general traits, not everything
                traits_to_include = ["CED", "BW", "WW", "YW", "Milk", "DollarM", "DollarB"]
            
            out.append(build_bull_payload(match.iloc[0], include_traits=traits_to_include))
    return {"bulls": out}

def filter_bulls_tool(trait: str, min_value: float = None, max_value: float = None, top_n: int = 5) -> Dict[str, Any]:
    """Filter bulls by a trait range and return top N."""
    if trait not in bulls_columns:
        return {"error": f"Trait '{trait}' not found in dataset"}
    
    df = bulls.dropna(subset=[trait]).copy()
    
    if min_value is not None:
        df = df[df[trait] >= min_value]
    if max_value is not None:
        df = df[df[trait] <= max_value]
    
    # Sort descending unless trait is BW (lower is better for birth weight)
    asc = trait == "BW"
    df = df.sort_values(by=trait, ascending=asc).head(top_n)
    
    return {
        "trait": trait,
        "bulls": [build_bull_payload(row) for _, row in df.iterrows()]
    }

def dispatch_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Route tool calls to appropriate functions."""
    if tool_name == "get_top_bulls":
        return get_top_bulls_tool(
            goal=tool_input.get("goal", "general"),
            top_n=tool_input.get("top_n", 3)
        )
    elif tool_name == "compare_bulls":
        return compare_bulls_tool(
            bull_names=tool_input.get("bull_names", []),
            focus_traits=tool_input.get("focus_traits")
        )
    elif tool_name == "filter_bulls":
        return filter_bulls_tool(
            trait=tool_input.get("trait"),
            min_value=tool_input.get("min_value"),
            max_value=tool_input.get("max_value"),
            top_n=tool_input.get("top_n", 5)
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}

# ============================================================
# 🔍 FALLBACK & VALIDATION
# ============================================================
def validate_reply_names(reply: str) -> bool:
    """Check if reply contains real bull names."""
    if not reply or not reply.strip():
        return False
    reply_lower = reply.lower()
    found = sum(1 for name in BULL_NAMES_SET if name in reply_lower)
    return found > 0

def fix_claude_formatting(text: str) -> str:
    """
    Post-process Claude's response to fix formatting issues.
    Claude keeps adding line breaks after colons - this removes them.
    Also converts $ shortcuts to full DollarX names for consistency.
    """
    import re
    
    # Fix: "Pen 1 – ECLIPSE\n(See catalog" → "Pen 1 – ECLIPSE (See catalog"
    text = re.sub(r'\*\*Pen \d+ – ([^\*]+)\*\*\s*\n\s*\(See catalog', r'**Pen \1** (See catalog', text)
    
    # Fix: "Key EPDs:\nCED:" → "Key EPDs: CED:"
    text = re.sub(r'\*\*Key EPDs:\*\*\s*\n\s*', r'**Key EPDs:** ', text)
    
    # Fix: "Dollar indexes:\nDollarM:" → "Dollar indexes: DollarM:"
    text = re.sub(r'\*\*Dollar indexes:\*\*\s*\n\s*', r'**Dollar indexes:** ', text)
    
    # Fix: "Why I recommend:\nText" → "Why I recommend: Text"  
    text = re.sub(r'\*\*Why I recommend:\*\*\s*\n\s*', r'**Why I recommend:** ', text)
    
    # Fix: "Best for:\nText" → "Best for: Text"
    text = re.sub(r'\*\*Best for:\*\*\s*\n\s*', r'**Best for:** ', text)
    
    # Fix: "Trade-off:\nText" → "Trade-off: Text"
    text = re.sub(r'\*\*Trade-off:\*\*\s*\n\s*', r'**Trade-off:** ', text)
    
    # Convert dollar sign shortcuts to full names for consistency
    # $M → DollarM, $B → DollarB, etc.
    text = text.replace('$M', 'DollarM')
    text = text.replace('$B', 'DollarB')
    text = text.replace('$C', 'DollarC')
    text = text.replace('$W', 'DollarW')
    text = text.replace('$EN', 'DollarEN')
    
    return text

def render_markdown_from_payload(payload: Dict[str, Any]) -> str:
    """
    Convert tool payload to formatted markdown using pre-formatted blocks.
    This is the fallback renderer when Claude doesn't respond.
    """
    bulls_list = payload.get("bulls", [])
    if not bulls_list:
        return "No bulls match your criteria."
    
    # Use the pre-formatted blocks directly
    blocks = [b.get("formatted_block", "") for b in bulls_list if b.get("formatted_block")]
    
    # Join with horizontal rule separator
    return "\n\n---\n\n".join(blocks)

# ============================================================
# 💬 WELCOME + STATE
# ============================================================
welcome_text = """
<div class='welcome-intro'>
<b>Welcome to the Close Enough Cattle Co. Bull Sale.</b><br>
I'm here to help you quickly explore our sale lineup and identify bulls that fit your operation's breeding objectives. Think of me as your digital assistant—I can answer questions about EPDs, traits, and rankings, but I'm a complement to, <b>NOT a replacement</b> for, reviewing the full sale catalog and working directly with our team.
</div>
<div class='example-questions'>
<b>Try asking me questions like:</b>
<div style='margin-top:0.5rem;line-height:1.6;'>
• Which bulls rank highest in DollarC for all-around commercial value?<br>
• I need calving ease for first-calf heifers—what bulls also offer strong growth performance?<br>
• Show me bulls that excel in fertility, milk, and maternal longevity.<br>
• Which bulls will improve my carcass value and marbling for better feedlot returns?<br>
• Compare your top-ranked DollarM and DollarB bulls for maternal vs. feedlot profit.
</div>
</div>
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role":"assistant","content": welcome_text},
    ]

# Render chat history
for m in st.session_state.messages:
    message_bubble(m["role"], m["content"])

# ============================================================
# 🧠 CLAUDE TOOL-CALLING LOOP (UP TO 5 CHAINED CALLS)
# ============================================================
def run_agent(user_message: str) -> str:
    """
    Execute Claude with tool-calling. The loop handles up to 5 tool calls
    and feeds the tool results back to the model.
    """
    # Build conversation history for Claude
    messages = []
    
    # Add chat history (skip the welcome message)
    for msg in st.session_state.messages[1:]:
        if msg["role"] in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # Add goal hint as part of the system prompt
    goal_hint = pick_goal(user_message)
    system_with_hint = f"{system_prompt}\n\n{RENDER_RULES}\n\nUse tools; start with get_top_bulls(goal='{goal_hint}', top_n=3) when appropriate."
    
    try:
        # Initial request to Claude
        response = client.messages.create(
            model=MODEL_PRIMARY,
            max_tokens=4096,
            system=system_with_hint,
            messages=messages,
            tools=TOOLS_SCHEMA,
            temperature=0.3,
        )
    except Exception as e:
        # Fallback to simpler model without tools
        try:
            response = client.messages.create(
                model=MODEL_FALLBACK,
                max_tokens=2048,
                system=system_with_hint,
                messages=messages,
                temperature=0.3,
            )
            # Extract text from response
            for block in response.content:
                if block.type == "text":
                    return block.text
            return "I apologize, but I encountered an error processing your request."
        except Exception:
            return f"⚠️ Error: {str(e)}"
    
    # Tool use loop (up to 5 iterations)
    step = 0
    max_steps = 5
    
    while step < max_steps:
        # Check if we got a final text response
        if response.stop_reason == "end_turn":
            # Extract text content
            text_content = []
            for block in response.content:
                if block.type == "text":
                    text_content.append(block.text)
            return "\n".join(text_content) if text_content else ""
        
        # Check for tool use
        if response.stop_reason == "tool_use":
            # Process tool calls
            tool_results = []
            
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id
                    
                    # Execute the tool
                    result = dispatch_tool(tool_name, tool_input)
                    
                    # Add tool result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result)
                    })
            
            # Add assistant's response (with tool use) to messages
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Add tool results to messages
            messages.append({
                "role": "user",
                "content": tool_results
            })
            
            # Continue conversation with tool results
            try:
                response = client.messages.create(
                    model=MODEL_PRIMARY,
                    max_tokens=4096,
                    system=system_with_hint,
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    temperature=0.3,
                )
            except Exception:
                break
            
            step += 1
        else:
            # Unexpected stop reason
            break
    
    # Extract final text if we exited the loop
    text_content = []
    for block in response.content:
        if block.type == "text":
            text_content.append(block.text)
    return "\n".join(text_content) if text_content else "I've analyzed the data but couldn't generate a response."

# ============================================================
# 💬 CHAT INPUT HANDLER (NO FILLER; GUARANTEED OUTPUT)
# ============================================================
prompt = st.chat_input("What breeding objectives are you focusing on this year?")
if prompt:
    # Increment query counter for rate limiting
    st.session_state.query_count += 1
    
    message_bubble("user", prompt)
    st.session_state.messages.append({"role":"user","content":prompt})

    # Spinner for UX; suppresses filler
    with st.spinner("🔍 Analyzing the sale data for the best matches..."):
        try:
            reply = run_agent(prompt)
        except Exception as e:
            reply = f"⚠️ Error: {e}"

    # If model is silent or names are invalid, do deterministic fallback
    if not reply or not reply.strip() or not validate_reply_names(reply):
        goal_hint = pick_goal(prompt)
        payload = get_top_bulls_tool(goal_hint, top_n=3)
        reply = render_markdown_from_payload(payload)
    
    # Fix Claude's formatting issues (removes unwanted line breaks after colons)
    reply = fix_claude_formatting(reply)

    message_bubble("assistant", reply)
    st.session_state.messages.append({"role":"assistant","content":reply})
