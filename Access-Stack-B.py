"""
sfm.py  --  SupportLabs Messenger
A polished PyQt5 chat + agent desktop application.
Providers: Ollama (live discovery), NIM, Groq, Anthropic, Gemini.
No emoji anywhere. ASCII/keyboard symbols only.
"""

import sys
import os
import json
import time
import uuid
import datetime
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Callable

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox,
    QSplitter, QFrame, QScrollArea, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QStatusBar, QSizePolicy,
    QTextBrowser, QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QSpinBox, QSlider, QCheckBox, QStackedWidget, QDialog,
    QDialogButtonBox, QProgressBar, QToolButton
)
from PyQt5.QtCore import (
    Qt, QThread, QObject, pyqtSignal, QTimer, QSize, QEvent, QProcess
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QTextCursor, QIcon, QTextCharFormat, QKeySequence
)
from PyQt5.QtWidgets import QShortcut

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from timer import start_session, log_usage, get_summary as timer_summary
except ImportError:
    def start_session(): pass
    def log_usage(m, t, **kw): pass
    def timer_summary(): return "No metrics yet."

try:
    from tools import run_calculator, run_web_search, run_file_reader
except ImportError:
    def run_calculator(expr):
        try:
            return str(eval(expr, {"__builtins__": {}}))
        except Exception as e:
            return f"Calc error: {e}"
    def run_web_search(q): return f"Web search not available (query: {q})"
    def run_file_reader(p):
        try:
            return Path(p).read_text(errors="replace")[:4000]
        except Exception as e:
            return f"File read error: {e}"


# ══════════════════════════════════════════════════════════════════
# SETTINGS STORE
# ══════════════════════════════════════════════════════════════════

SETTINGS_FILE = Path("sfm_settings.json")
CONVERSATIONS_FILE = Path("sfm_conversations.json")
RUNS_DIR = Path("sfm_runs")

DEFAULT_SETTINGS = {
    "groq_key": "",
    "anthropic_key": "",
    "gemini_key": "",
    "nim_key": "",
    "nim_base": "http://localhost:8000/v1",
    "ollama_base": "http://localhost:11434",
    "default_model_provider": "ollama",
    "default_model": "",
    "default_system": "You are a helpful assistant. Be clear, concise, and friendly.",
    "font_size": 13,
    "accent": "#4f8ef7",
}

_settings: Dict = {}

def load_settings() -> Dict:
    global _settings
    if SETTINGS_FILE.exists():
        try:
            _settings = {**DEFAULT_SETTINGS, **json.loads(SETTINGS_FILE.read_text())}
        except Exception:
            _settings = dict(DEFAULT_SETTINGS)
    else:
        _settings = dict(DEFAULT_SETTINGS)
    # Env overrides
    for env, key in [("GROQ_API_KEY","groq_key"),("ANTHROPIC_API_KEY","anthropic_key"),
                     ("GEMINI_API_KEY","gemini_key"),("NIM_API_KEY","nim_key"),
                     ("NIM_API_BASE","nim_base"),("OLLAMA_BASE","ollama_base")]:
        v = os.environ.get(env,"")
        if v:
            _settings[key] = v
    return _settings

def save_settings(s: Dict):
    global _settings
    _settings = s
    try:
        SETTINGS_FILE.write_text(json.dumps(s, indent=2))
    except Exception:
        pass

def S(key: str, default=None):
    return _settings.get(key, DEFAULT_SETTINGS.get(key, default))


# ══════════════════════════════════════════════════════════════════
# PALETTE
# ══════════════════════════════════════════════════════════════════

COLORS = {
    "bg":        "#0d0f14",
    "panel":     "#131620",
    "surface":   "#1b1f2e",
    "border":    "#252a3d",
    "accent":    "#4f8ef7",
    "accent2":   "#7c3aed",
    "green":     "#22d3a5",
    "yellow":    "#f59e0b",
    "red":       "#ef4444",
    "text":      "#e2e8f0",
    "muted":     "#64748b",
    "user_bg":   "#1e3a5f",
    "asst_bg":   "#1b1f2e",
}

def STYLESHEET(font_size=13, accent="#4f8ef7"):
    C = {**COLORS, "accent": accent}
    return f"""
QMainWindow, QWidget {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: {font_size}px;
}}
QTabWidget::pane {{
    border: 1px solid {C['border']};
    background: {C['panel']};
    border-radius: 6px;
    top: -1px;
}}
QTabWidget::tab-bar {{
    alignment: center;
}}
QTabBar::tab {{
    background: {C['surface']};
    color: {C['muted']};
    padding: 9px 28px;
    border: 1px solid {C['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
    font-size: {font_size - 1}px;
    font-weight: 500;
    min-width: 90px;
}}
QTabBar::tab:selected {{
    background: {C['panel']};
    color: {C['accent']};
    border-bottom: 2px solid {C['accent']};
}}
QTabBar::tab:hover:!selected {{
    color: {C['text']};
    background: {C['border']};
}}
QPushButton {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    padding: 7px 16px;
    font-size: {font_size - 1}px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {C['border']};
    border-color: {C['accent']};
    color: {C['accent']};
}}
QPushButton:pressed {{
    background-color: {C['accent']};
    color: white;
}}
QPushButton:disabled {{
    color: {C['muted']};
    border-color: {C['border']};
    background: {C['surface']};
}}
QPushButton#primary {{
    background-color: {C['accent']};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: #3b7de8;
}}
QPushButton#danger {{
    border-color: {C['red']};
    color: {C['red']};
    background: transparent;
}}
QPushButton#stop {{
    background-color: {C['red']};
    color: white;
    border: none;
    font-weight: 600;
}}
QTextEdit, QLineEdit {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    padding: 6px 10px;
    selection-background-color: {C['accent']};
}}
QTextEdit:focus, QLineEdit:focus {{
    border-color: {C['accent']};
}}
QComboBox {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    padding: 6px 10px;
    min-width: 140px;
}}
QComboBox::drop-down {{ border: none; padding-right: 8px; }}
QComboBox QAbstractItemView {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    selection-background-color: {C['accent']};
}}
QGroupBox {{
    border: 1px solid {C['border']};
    border-radius: 6px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    font-weight: 600;
    color: {C['muted']};
    font-size: {font_size - 2}px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}}
QTableWidget {{
    background-color: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    gridline-color: {C['border']};
    selection-background-color: {C['accent']};
}}
QHeaderView::section {{
    background-color: {C['panel']};
    color: {C['muted']};
    border: none;
    border-bottom: 1px solid {C['border']};
    padding: 6px 10px;
    font-size: {font_size - 2}px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QScrollBar:vertical {{
    background: {C['panel']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['muted']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {C['panel']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {C['border']};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QStatusBar {{
    background: {C['panel']};
    color: {C['muted']};
    border-top: 1px solid {C['border']};
    font-size: {font_size - 2}px;
}}
QListWidget {{
    background: {C['panel']};
    color: {C['text']};
    border: none;
    border-radius: 4px;
    font-size: {font_size - 1}px;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {C['border']};
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background: {C['surface']};
    color: {C['accent']};
}}
QListWidget::item:hover:!selected {{
    background: {C['border']};
}}
QSlider::groove:horizontal {{
    background: {C['border']};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {C['accent']};
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}}
QSlider::sub-page:horizontal {{
    background: {C['accent']};
    border-radius: 2px;
}}
QCheckBox {{
    color: {C['text']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 2px solid {C['border']};
    border-radius: 3px;
    background: {C['surface']};
}}
QCheckBox::indicator:checked {{
    background: {C['accent']};
    border-color: {C['accent']};
}}
QSpinBox {{
    background: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    padding: 4px 8px;
}}
QProgressBar {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    height: 6px;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {C['accent']};
    border-radius: 4px;
}}
QFrame#divider {{
    background: {C['border']};
    max-height: 1px;
    border: none;
}}
"""


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def make_label(text, size=None, color=None, bold=False, muted=False):
    lbl = QLabel(text)
    style_parts = []
    if size:
        style_parts.append(f"font-size:{size}px;")
    if color:
        style_parts.append(f"color:{color};")
    elif muted:
        style_parts.append(f"color:{COLORS['muted']};")
    if bold:
        style_parts.append("font-weight:700;")
    if style_parts:
        lbl.setStyleSheet(" ".join(style_parts))
    return lbl

def make_divider():
    line = QFrame()
    line.setObjectName("divider")
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"background:{COLORS['border']};max-height:1px;border:none;")
    return line

def make_button(text, obj_name=None, tooltip=None):
    btn = QPushButton(text)
    if obj_name:
        btn.setObjectName(obj_name)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn

def md_to_html(text: str) -> str:
    """Minimal Markdown -> HTML for chat display."""
    import re
    # Escape HTML first
    text = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    # Fenced code blocks
    def code_block(m):
        lang = m.group(1) or ""
        code = m.group(2)
        return (f'<pre style="background:#0d1117;color:#22d3a5;padding:10px 14px;'
                f'border-radius:6px;font-family:monospace;font-size:12px;'
                f'overflow-x:auto;margin:6px 0;">'
                f'<code>{code}</code></pre>')
    text = re.sub(r'```(\w*)\n?([\s\S]*?)```', code_block, text)
    # Inline code
    text = re.sub(r'`([^`]+)`',
        r'<code style="background:#1b1f2e;color:#22d3a5;padding:1px 5px;border-radius:3px;font-family:monospace;">\1</code>',
        text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    # Headers
    text = re.sub(r'^### (.+)$', r'<h4 style="color:#e2e8f0;margin:8px 0 4px;">\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h3 style="color:#e2e8f0;margin:10px 0 4px;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h2 style="color:#e2e8f0;margin:12px 0 6px;">\1</h2>', text, flags=re.MULTILINE)
    # Unordered lists (simple)
    text = re.sub(r'^\s*[-*] (.+)$', r'<li style="margin:2px 0;">\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li.*</li>)', r'<ul style="margin:6px 0;padding-left:20px;">\1</ul>', text, flags=re.DOTALL)
    # Newlines
    text = text.replace("\n", "<br>")
    # Clean up double br around block elements
    text = re.sub(r'<br>(<(?:pre|ul|h[2-4]))', r'\1', text)
    text = re.sub(r'(</(?:pre|ul|h[2-4])>)<br>', r'\1', text)
    return text

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ══════════════════════════════════════════════════════════════════
# PROVIDER CALLERS
# ══════════════════════════════════════════════════════════════════

def get_ollama_models() -> List[str]:
    base = S("ollama_base", "http://localhost:11434")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=3) as r:
            data = json.loads(r.read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []

def call_ollama(model: str, messages: List[Dict], system: str,
                stream_cb: Optional[Callable] = None) -> str:
    base = S("ollama_base", "http://localhost:11434")
    api_msgs = []
    if system:
        api_msgs.append({"role": "system", "content": system})
    api_msgs.extend(messages)
    payload = {"model": model, "messages": api_msgs, "stream": stream_cb is not None}
    req = urllib.request.Request(
        f"{base}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        if stream_cb:
            full = ""
            with urllib.request.urlopen(req, timeout=120) as r:
                for raw in r:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            full += token
                            stream_cb(token)
                    except json.JSONDecodeError:
                        pass
            return full
        else:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())["message"]["content"]
    except ConnectionRefusedError:
        return "[!] Ollama not running -- start with: ollama serve"
    except Exception as e:
        return f"[!] Ollama error: {e}"

def call_groq(model: str, messages: List[Dict], system: str,
              stream_cb: Optional[Callable] = None) -> str:
    key = S("groq_key") or os.environ.get("GROQ_API_KEY","")
    if not key:
        return "[!] Groq API key not set -- add it in Settings"
    api_msgs = []
    if system:
        api_msgs.append({"role": "system", "content": system})
    api_msgs.extend(messages)
    payload = {"model": model, "messages": api_msgs, "temperature": 0.7, "max_tokens": 4096}
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())["choices"][0]["message"]["content"]
            if stream_cb:
                stream_cb(result)
            return result
    except Exception as e:
        return f"[!] Groq error: {e}"

def call_anthropic(model: str, messages: List[Dict], system: str,
                   stream_cb: Optional[Callable] = None) -> str:
    key = S("anthropic_key") or os.environ.get("ANTHROPIC_API_KEY","")
    if not key:
        return "[!] Anthropic API key not set -- add it in Settings"
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=key)
        msg = client.messages.create(
            model=model or "claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=messages
        )
        result = msg.content[0].text
        if stream_cb:
            stream_cb(result)
        return result
    except ImportError:
        return "[!] anthropic SDK not installed: pip install anthropic"
    except Exception as e:
        return f"[!] Anthropic error: {e}"

def call_gemini(model: str, messages: List[Dict], system: str,
                stream_cb: Optional[Callable] = None) -> str:
    key = S("gemini_key") or os.environ.get("GEMINI_API_KEY","")
    if not key:
        return "[!] Gemini API key not set -- add it in Settings"
    user_text = " ".join(m["content"] for m in messages if m["role"]=="user")
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        gmodel = genai.GenerativeModel(model_name=model, system_instruction=system)
        response = gmodel.generate_content(user_text)
        result = response.text
    except ImportError:
        # REST fallback
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        payload = {
            "system_instruction":{"parts":[{"text":system}]},
            "contents":[{"parts":[{"text":user_text}]}],
            "generationConfig":{"maxOutputTokens":4096,"temperature":0.7}
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"[!] Gemini REST error: {e}"
    except Exception as e:
        return f"[!] Gemini error: {e}"
    if stream_cb:
        stream_cb(result)
    return result

def call_nim(model: str, messages: List[Dict], system: str,
             stream_cb: Optional[Callable] = None) -> str:
    key = S("nim_key") or os.environ.get("NIM_API_KEY","not-needed")
    base = S("nim_base","http://localhost:8000/v1")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, base_url=base)
        api_msgs = []
        if system:
            api_msgs.append({"role":"system","content":system})
        api_msgs.extend(messages)
        response = client.chat.completions.create(
            model=model, temperature=0.7, max_tokens=4096, messages=api_msgs
        )
        result = response.choices[0].message.content
        if stream_cb:
            stream_cb(result)
        return result
    except ImportError:
        return "[!] openai SDK not installed: pip install openai"
    except Exception as e:
        return f"[!] NIM error: {e}"

PROVIDERS = {
    "ollama":    {"label": "Ollama (local)", "caller": call_ollama,
                  "models": []},
    "nim":       {"label": "NVIDIA NIM",     "caller": call_nim,
                  "models": ["meta/llama3-70b-instruct","mistralai/mistral-7b-instruct-v0.3","nvidia/llama-3.1-nemotron-70b-instruct"]},
    "groq":      {"label": "Groq",           "caller": call_groq,
                  "models": ["llama3-70b-8192","mixtral-8x7b-32768","llama-3.1-8b-instant","gemma2-9b-it"]},
    "anthropic": {"label": "Anthropic",      "caller": call_anthropic,
                  "models": ["claude-sonnet-4-6","claude-opus-4-6","claude-haiku-4-5-20251001"]},
    "gemini":    {"label": "Google Gemini",  "caller": call_gemini,
                  "models": ["gemini-2.0-flash","gemini-2.5-flash-preview-05-20","gemini-1.5-pro"]},
}

def call_provider(provider: str, model: str, messages: List[Dict], system: str,
                  stream_cb: Optional[Callable] = None) -> str:
    p = PROVIDERS.get(provider)
    if not p:
        return f"[!] Unknown provider: {provider}"
    return p["caller"](model, messages, system, stream_cb)


# ══════════════════════════════════════════════════════════════════
# WORKER THREADS
# ══════════════════════════════════════════════════════════════════

class ChatWorker(QThread):
    token = pyqtSignal(str)
    finished = pyqtSignal(str, float)
    error = pyqtSignal(str)

    def __init__(self, provider, model, messages, system):
        super().__init__()
        self.provider = provider
        self.model = model
        self.messages = messages
        self.system = system
        self._stop = False
        self._full = ""

    def run(self):
        t0 = time.time()
        try:
            def stream_cb(tok):
                if self._stop:
                    raise InterruptedError("stopped")
                self._full += tok
                self.token.emit(tok)

            result = call_provider(self.provider, self.model, self.messages,
                                   self.system, stream_cb)
            if not self._full:
                # non-streaming provider emitted all at once via stream_cb
                self._full = result
                if result:
                    self.token.emit(result)
        except InterruptedError:
            pass
        except Exception as e:
            self.error.emit(str(e))
        elapsed = time.time() - t0
        try:
            log_usage(f"{self.provider}/{self.model}", elapsed)
        except Exception:
            pass
        self.finished.emit(self._full, elapsed)

    def stop(self):
        self._stop = True


class AgentWorker(QThread):
    step = pyqtSignal(dict)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    TOOL_DEFS = {
        "calculator": {
            "desc": "Evaluate a mathematical expression. Input: the expression as a string.",
            "fn": run_calculator,
        },
        "web_search": {
            "desc": "Search the web for information. Input: search query string.",
            "fn": run_web_search,
        },
        "file_reader": {
            "desc": "Read contents of a file on disk. Input: absolute or relative file path.",
            "fn": run_file_reader,
        },
    }

    def __init__(self, goal, provider, model, system, tools_enabled, max_iter):
        super().__init__()
        self.goal = goal
        self.provider = provider
        self.model = model
        self.system = system
        self.tools_enabled = tools_enabled
        self.max_iter = max_iter
        self._stop = False

    def run(self):
        active_tools = {k: v for k, v in self.TOOL_DEFS.items() if k in self.tools_enabled}
        tool_desc = "\n".join(f"- {k}: {v['desc']}" for k, v in active_tools.items())
        agent_system = (
            f"{self.system}\n\n"
            "You are an agent with access to tools. For each step, output either:\n"
            "  TOOL: <tool_name>\n  INPUT: <input>\n"
            "or when done:\n"
            "  FINAL: <your final answer>\n\n"
            f"Available tools:\n{tool_desc or '(none enabled)'}\n\n"
            "Think step by step. Use tools when helpful. Be concise."
        )
        messages = [{"role":"user","content":f"Goal: {self.goal}"}]
        history = []
        final = ""

        for iteration in range(self.max_iter):
            if self._stop:
                break
            t0 = time.time()
            response = call_provider(self.provider, self.model, messages, agent_system)
            elapsed_ms = int((time.time() - t0) * 1000)

            # Parse response
            tool_name = ""
            tool_input = ""
            lines = response.strip().splitlines()
            mode = None
            for line in lines:
                ls = line.strip()
                if ls.startswith("TOOL:"):
                    tool_name = ls[5:].strip()
                    mode = "tool"
                elif ls.startswith("INPUT:") and mode == "tool":
                    tool_input = ls[6:].strip()
                elif ls.startswith("FINAL:"):
                    final = ls[6:].strip()
                    if not final:
                        # rest of lines
                        idx = lines.index(line)
                        final = "\n".join(lines[idx+1:]).strip() or line[6:].strip()
                    mode = "final"
                    break

            if mode == "final" or "FINAL:" in response:
                if not final:
                    final = response.replace("FINAL:","").strip()
                self.step.emit({
                    "step": iteration + 1,
                    "tool": "--",
                    "input": "(done)",
                    "output": final[:200],
                    "ms": elapsed_ms,
                })
                break

            if mode == "tool" and tool_name in active_tools:
                tool_fn = active_tools[tool_name]["fn"]
                try:
                    tool_output = str(tool_fn(tool_input))
                except Exception as e:
                    tool_output = f"Tool error: {e}"
                self.step.emit({
                    "step": iteration + 1,
                    "tool": tool_name,
                    "input": tool_input[:100],
                    "output": tool_output[:200],
                    "ms": elapsed_ms,
                })
                # Append to conversation
                messages.append({"role":"assistant","content":response})
                messages.append({"role":"user","content":f"Tool result ({tool_name}): {tool_output}\nContinue."})
                history.append({"tool":tool_name,"input":tool_input,"output":tool_output})
            else:
                # Model responded without proper format -- treat as final
                final = response
                self.step.emit({
                    "step": iteration + 1,
                    "tool": "--",
                    "input": "(unstructured response)",
                    "output": response[:200],
                    "ms": elapsed_ms,
                })
                break

        if not final:
            final = "(Agent reached max iterations without a final answer.)"
        self.finished.emit(final)

    def stop(self):
        self._stop = True


# ══════════════════════════════════════════════════════════════════
# SYSTEM PROMPT PRESETS
# ══════════════════════════════════════════════════════════════════

SYSTEM_PRESETS = {
    "Assistant": "You are a helpful, friendly, and clear AI assistant.",
    "Coder": (
        "You are an expert software engineer. Provide clean, well-commented code. "
        "Explain trade-offs. Use fenced code blocks with language tags."
    ),
    "Analyst": (
        "You are a rigorous data and business analyst. Be precise, cite sources when "
        "possible, structure responses with clear sections, and highlight uncertainties."
    ),
    "Critic": (
        "You are a thoughtful critic and editor. Challenge assumptions, identify weaknesses, "
        "offer specific improvements, and be direct but constructive."
    ),
    "Socratic": (
        "You are a Socratic tutor. Guide the user to understanding through questions "
        "rather than direct answers. Encourage their own reasoning."
    ),
    "Custom": "",
}


# ══════════════════════════════════════════════════════════════════
# CHAT BUBBLE RENDERER
# ══════════════════════════════════════════════════════════════════

class ChatRenderer:
    """Builds HTML for the chat QTextBrowser."""

    BUBBLE_USER = f"""
    <div style="margin:8px 0;display:flex;justify-content:flex-end;">
      <div style="max-width:85%;background:{COLORS['user_bg']};border-radius:14px 14px 4px 14px;
           padding:10px 14px;color:{COLORS['text']};font-size:13px;line-height:1.55;">
        <div style="font-size:10px;color:{COLORS['muted']};margin-bottom:4px;text-align:right;">
          You &nbsp;|&nbsp; {{time}}
        </div>
        {{content}}
      </div>
    </div>"""

    BUBBLE_ASST = f"""
    <div style="margin:8px 0;display:flex;justify-content:flex-start;" id="{{bubble_id}}">
      <div style="max-width:85%;background:{COLORS['asst_bg']};border:1px solid {COLORS['border']};
           border-radius:14px 14px 14px 4px;padding:10px 14px;color:{COLORS['text']};
           font-size:13px;line-height:1.55;">
        <div style="font-size:10px;color:{COLORS['muted']};margin-bottom:4px;">
          {{model}} &nbsp;|&nbsp; {{time}}
        </div>
        {{content}}
        <div style="font-size:10px;color:{COLORS['muted']};margin-top:6px;text-align:right;">
          {{tokens}} tokens &nbsp; {{elapsed}}
        </div>
      </div>
    </div>"""

    BUBBLE_TYPING = f"""
    <div style="margin:8px 0;display:flex;justify-content:flex-start;" id="typing_indicator">
      <div style="background:{COLORS['asst_bg']};border:1px solid {COLORS['border']};
           border-radius:14px;padding:10px 18px;color:{COLORS['muted']};font-size:13px;">
        &nbsp; . . . &nbsp;
      </div>
    </div>"""

    @staticmethod
    def user_bubble(content: str) -> str:
        t = datetime.datetime.now().strftime("%H:%M")
        return ChatRenderer.BUBBLE_USER.format(
            time=t,
            content=md_to_html(content)
        )

    @staticmethod
    def asst_bubble(content: str, model: str, elapsed: float, bubble_id: str) -> str:
        t = datetime.datetime.now().strftime("%H:%M")
        toks = estimate_tokens(content)
        return ChatRenderer.BUBBLE_ASST.format(
            bubble_id=bubble_id,
            time=t,
            model=model,
            content=md_to_html(content),
            tokens=toks,
            elapsed=f"{elapsed:.1f}s" if elapsed > 0 else ""
        )

    @staticmethod
    def typing_bubble() -> str:
        return ChatRenderer.BUBBLE_TYPING


# ══════════════════════════════════════════════════════════════════
# MODEL SELECTOR WIDGET
# ══════════════════════════════════════════════════════════════════

class ModelSelector(QWidget):
    model_changed = pyqtSignal(str, str)  # (provider, model)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl_p = make_label("Provider:", muted=True)
        layout.addWidget(lbl_p)
        self.provider_cb = QComboBox()
        for key, info in PROVIDERS.items():
            self.provider_cb.addItem(info["label"], key)
        layout.addWidget(self.provider_cb)

        lbl_m = make_label("Model:", muted=True)
        layout.addWidget(lbl_m)
        self.model_cb = QComboBox()
        self.model_cb.setMinimumWidth(200)
        layout.addWidget(self.model_cb)

        self.refresh_btn = make_button("[~] Refresh")
        self.refresh_btn.setFixedWidth(90)
        self.refresh_btn.setToolTip("Reload Ollama model list")
        self.refresh_btn.clicked.connect(self._refresh_models)
        layout.addWidget(self.refresh_btn)

        layout.addStretch()

        self.provider_cb.currentIndexChanged.connect(self._on_provider_changed)
        self._on_provider_changed(0)

    def _on_provider_changed(self, _=None):
        provider = self.provider_cb.currentData()
        self.model_cb.clear()
        if provider == "ollama":
            models = get_ollama_models()
            if not models:
                models = ["(no models -- run: ollama pull llama3)"]
        else:
            models = PROVIDERS[provider]["models"]
        for m in models:
            self.model_cb.addItem(m)
        self._emit()

    def _refresh_models(self):
        self._on_provider_changed()

    def _emit(self):
        self.model_changed.emit(self.get_provider(), self.get_model())

    def get_provider(self) -> str:
        return self.provider_cb.currentData() or "ollama"

    def get_model(self) -> str:
        return self.model_cb.currentText()

    def set_provider_model(self, provider: str, model: str):
        idx = self.provider_cb.findData(provider)
        if idx >= 0:
            self.provider_cb.setCurrentIndex(idx)
        midx = self.model_cb.findText(model)
        if midx >= 0:
            self.model_cb.setCurrentIndex(midx)


# ══════════════════════════════════════════════════════════════════
# TAB: CHAT
# ══════════════════════════════════════════════════════════════════

class ChatTab(QWidget):
    status_update = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[ChatWorker] = None
        self.conversations: Dict[str, Dict] = {}
        self.active_conv_id: Optional[str] = None
        self._streaming_bubble_id: Optional[str] = None
        self._streaming_content: str = ""
        self._stream_model: str = ""
        self._stream_t0: float = 0.0
        self._setup_ui()
        self._load_conversations()
        if not self.conversations:
            self._new_conversation()

    # ---- Layout ----

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Horizontal splitter so the user can drag the sidebar wider/narrower
        self._main_splitter = QSplitter(Qt.Horizontal)
        self._main_splitter.setHandleWidth(3)
        self._main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {COLORS['border']};
            }}
            QSplitter::handle:hover {{
                background: {COLORS['accent']};
            }}
        """)

        # -- Left sidebar: conversation list --
        sidebar = QWidget()
        sidebar.setStyleSheet(f"background:{COLORS['panel']};")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 12, 10, 12)
        sb_layout.setSpacing(8)

        sb_title = QLabel("Conversations")
        sb_title.setStyleSheet(f"font-size:11px;color:{COLORS['muted']};letter-spacing:1px;text-transform:uppercase;font-weight:600;")
        sb_layout.addWidget(sb_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.new_conv_btn = make_button("[+] New")
        self.new_conv_btn.clicked.connect(self._new_conversation)
        self.del_conv_btn = make_button("[x] Del", "danger")
        self.del_conv_btn.clicked.connect(self._delete_conversation)
        btn_row.addWidget(self.new_conv_btn)
        btn_row.addWidget(self.del_conv_btn)
        sb_layout.addLayout(btn_row)

        self.conv_list = QListWidget()
        self.conv_list.currentItemChanged.connect(self._on_conv_selected)
        sb_layout.addWidget(self.conv_list, stretch=1)

        export_btn = make_button("[ Export ]")
        export_btn.clicked.connect(self._export_conversation)
        sb_layout.addWidget(export_btn)

        self._main_splitter.addWidget(sidebar)

        # -- Main chat area --
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # Model selector row
        self.model_sel = ModelSelector()
        main_layout.addWidget(self.model_sel)

        main_layout.addWidget(make_divider())

        # System prompt (collapsible toggle)
        sys_header = QHBoxLayout()
        sys_lbl = make_label("System Prompt", muted=True)
        sys_lbl.setStyleSheet(f"font-size:11px;color:{COLORS['muted']};letter-spacing:0.5px;font-weight:600;")
        sys_header.addWidget(sys_lbl)
        self.preset_cb = QComboBox()
        self.preset_cb.setMaximumWidth(150)
        for name in SYSTEM_PRESETS:
            self.preset_cb.addItem(name)
        self.preset_cb.currentTextChanged.connect(self._on_preset_changed)
        sys_header.addWidget(self.preset_cb)
        self.sys_toggle_btn = make_button("[^] Hide")
        self.sys_toggle_btn.setFixedWidth(80)
        self.sys_toggle_btn.clicked.connect(self._toggle_sys_prompt)
        sys_header.addWidget(self.sys_toggle_btn)
        sys_header.addStretch()
        main_layout.addLayout(sys_header)

        self.system_edit = QTextEdit()
        self.system_edit.setMaximumHeight(72)
        self.system_edit.setPlainText(S("default_system"))
        main_layout.addWidget(self.system_edit)
        self._sys_visible = True

        main_layout.addWidget(make_divider())

        # Chat display
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet(f"""
            QTextBrowser {{
                background:{COLORS['bg']};
                border:none;
                padding:8px;
                color:{COLORS['text']};
                font-size:{S('font_size',13)}px;
                line-height:1.6;
            }}
        """)
        self._rebuild_html()
        main_layout.addWidget(self.chat_display, stretch=1)

        # Input area
        input_frame = QWidget()
        input_frame.setStyleSheet(f"background:{COLORS['panel']};border-top:1px solid {COLORS['border']};")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(6)

        self.msg_input = QTextEdit()
        self.msg_input.setMaximumHeight(90)
        self.msg_input.setPlaceholderText("Type a message...  (Ctrl+Enter to send, Enter for newline)")
        self.msg_input.installEventFilter(self)
        self.msg_input.textChanged.connect(self._on_input_changed)
        input_layout.addWidget(self.msg_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        BTN_W = 96
        self.send_btn = make_button("Send  >>", "primary")
        self.send_btn.setFixedWidth(BTN_W)
        self.send_btn.clicked.connect(self._send)
        self.stop_btn = make_button("[ Stop ]", "stop")
        self.stop_btn.setFixedWidth(BTN_W)
        self.stop_btn.hide()
        self.stop_btn.clicked.connect(self._stop_generation)
        self.retry_btn = make_button("[ Retry ]")
        self.retry_btn.setFixedWidth(BTN_W)
        self.retry_btn.clicked.connect(self._regenerate)
        self.clear_btn = make_button("[ Clear ]")
        self.clear_btn.setFixedWidth(BTN_W)
        self.clear_btn.clicked.connect(self._clear_chat)

        self.token_lbl = make_label("0 / 4096 tokens", muted=True)
        self.token_lbl.setStyleSheet(f"font-size:11px;color:{COLORS['muted']};")

        btn_row.addWidget(self.send_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.retry_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.token_lbl)
        input_layout.addLayout(btn_row)

        main_layout.addWidget(input_frame)
        self._main_splitter.addWidget(main)
        self._main_splitter.setSizes([200, 1100])
        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)
        # Sidebar can shrink but not below something usable
        sidebar.setMinimumWidth(140)
        sidebar.setMaximumWidth(400)
        root.addWidget(self._main_splitter)

    # ---- Conversation management ----

    def _load_conversations(self):
        if CONVERSATIONS_FILE.exists():
            try:
                data = json.loads(CONVERSATIONS_FILE.read_text())
                self.conversations = data
                self._rebuild_conv_list()
                if self.conversations:
                    first_id = list(self.conversations.keys())[0]
                    self._switch_conversation(first_id)
            except Exception:
                pass

    def save_conversations(self):
        try:
            CONVERSATIONS_FILE.write_text(json.dumps(self.conversations, indent=2))
        except Exception:
            pass

    def _new_conversation(self):
        cid = str(uuid.uuid4())
        self.conversations[cid] = {
            "title": "New conversation",
            "provider": self.model_sel.get_provider() if hasattr(self,'model_sel') else "ollama",
            "model": self.model_sel.get_model() if hasattr(self,'model_sel') else "",
            "system": S("default_system",""),
            "messages": [],
            "created_at": datetime.datetime.now().isoformat(),
        }
        self._rebuild_conv_list()
        self._switch_conversation(cid)

    def _delete_conversation(self):
        if not self.active_conv_id:
            return
        reply = QMessageBox.question(self, "Delete Conversation",
            "Delete this conversation? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        del self.conversations[self.active_conv_id]
        self.active_conv_id = None
        self._rebuild_conv_list()
        if self.conversations:
            self._switch_conversation(list(self.conversations.keys())[0])
        else:
            self._new_conversation()

    def _rebuild_conv_list(self):
        self.conv_list.blockSignals(True)
        self.conv_list.clear()
        for cid, conv in reversed(list(self.conversations.items())):
            item = QListWidgetItem()
            title = conv.get("title","New conversation")
            model = conv.get("model","")
            item.setText(f"{title[:28]}\n  {model[:22]}")
            item.setData(Qt.UserRole, cid)
            self.conv_list.addItem(item)
        self.conv_list.blockSignals(False)
        # Re-select active
        if self.active_conv_id:
            for i in range(self.conv_list.count()):
                if self.conv_list.item(i).data(Qt.UserRole) == self.active_conv_id:
                    self.conv_list.setCurrentRow(i)
                    break

    def _on_conv_selected(self, current, _previous):
        if not current:
            return
        cid = current.data(Qt.UserRole)
        if cid != self.active_conv_id:
            self._switch_conversation(cid)

    def _switch_conversation(self, cid: str):
        self.active_conv_id = cid
        conv = self.conversations[cid]
        if hasattr(self, 'system_edit'):
            self.system_edit.setPlainText(conv.get("system", S("default_system","")))
        # Set model selector
        if hasattr(self, 'model_sel'):
            p = conv.get("provider","ollama")
            m = conv.get("model","")
            if m:
                self.model_sel.set_provider_model(p, m)
        self._rebuild_html()
        # Select in list
        for i in range(self.conv_list.count()):
            if self.conv_list.item(i).data(Qt.UserRole) == cid:
                self.conv_list.blockSignals(True)
                self.conv_list.setCurrentRow(i)
                self.conv_list.blockSignals(False)
                break

    def _active_conv(self) -> Optional[Dict]:
        return self.conversations.get(self.active_conv_id)

    # ---- HTML rendering ----

    def _rebuild_html(self):
        conv = self._active_conv()
        parts = ['<html><body style="font-family:\'Segoe UI\',sans-serif;background:#0d0f14;margin:0;padding:8px;">']
        if conv and conv["messages"]:
            for msg in conv["messages"]:
                if msg["role"] == "user":
                    parts.append(ChatRenderer.user_bubble(msg["content"]))
                elif msg["role"] == "assistant":
                    bid = msg.get("bubble_id", str(uuid.uuid4())[:8])
                    elapsed = msg.get("elapsed", 0.0)
                    model = msg.get("model", "")
                    parts.append(ChatRenderer.asst_bubble(msg["content"], model, elapsed, bid))
        else:
            # Friendly empty state -- shows when a conversation has no messages
            parts.append(f"""
            <div style="display:flex;flex-direction:column;align-items:center;
                        justify-content:center;height:300px;color:{COLORS['muted']};
                        font-family:'Segoe UI',sans-serif;">
              <div style="font-size:22px;color:{COLORS['text']};margin-bottom:8px;
                          letter-spacing:-0.5px;font-weight:600;">
                Ready when you are.
              </div>
              <div style="font-size:13px;color:{COLORS['muted']};margin-bottom:18px;">
                Type below to start a conversation.
              </div>
              <div style="font-size:11px;color:{COLORS['muted']};font-family:monospace;
                          opacity:0.7;line-height:1.8;text-align:center;">
                Ctrl+Enter to send &nbsp;&middot;&nbsp; Enter for newline<br>
                Ctrl+N for a new chat &nbsp;&middot;&nbsp; F11 to focus the chat
              </div>
            </div>
            """)
        parts.append('</body></html>')
        self.chat_display.setHtml("".join(parts))
        self.chat_display.moveCursor(QTextCursor.End)

    def _append_user_bubble(self, text: str):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
        # Append HTML -- easiest via rebuild for correctness
        self._rebuild_html()
        # Show typing indicator
        html = self.chat_display.toHtml()
        indicator = ChatRenderer.typing_bubble()
        # Insert before </body>
        html = html.replace("</body>", indicator + "</body>")
        self.chat_display.setHtml(html)
        self.chat_display.moveCursor(QTextCursor.End)

    def _start_asst_bubble(self, bubble_id: str):
        """Replace typing indicator with empty assistant bubble."""
        self._streaming_content = ""
        html = self.chat_display.toHtml()
        # Remove typing indicator
        import re
        html = re.sub(r'<div[^>]*id="typing_indicator"[^>]*>.*?</div>\s*</div>', '',
                      html, flags=re.DOTALL)
        model = f"{self.model_sel.get_provider()}/{self.model_sel.get_model()}"
        self._stream_model = model
        # Add empty bubble placeholder
        placeholder = ChatRenderer.asst_bubble("", model, 0.0, bubble_id)
        html = html.replace("</body>", placeholder + "</body>")
        self.chat_display.setHtml(html)
        self.chat_display.moveCursor(QTextCursor.End)

    def _append_token(self, token: str):
        self._streaming_content += token
        # OPTIMIZATION: Don't rebuild entire chat. Just update the streaming bubble.
        # Get current HTML and replace only the streaming bubble content.
        html = self.chat_display.toHtml()
        if not html:
            return
        
        model = self._stream_model
        bid = self._streaming_bubble_id or "stream"
        elapsed = time.time() - self._stream_t0
        
        # Build ONLY the streaming bubble HTML (not the entire page)
        streaming_bubble = ChatRenderer.asst_bubble(self._streaming_content, model, elapsed, bid)
        
        # Find and replace the streaming bubble in the existing HTML.
        # Pattern: find the div with id matching our bubble_id and replace its content.
        import re
        pattern = rf'(<div[^>]*id="{re.escape(bid)}"[^>]*>.*?</div>\s*</div>)'
        replacement = streaming_bubble
        
        new_html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)
        
        # If no match (first token), append before </body>
        if new_html == html:
            new_html = html.replace("</body>", streaming_bubble + "</body>")
        
        self.chat_display.setHtml(new_html)
        self.chat_display.moveCursor(QTextCursor.End)

    # ---- Send / receive ----

    def _send(self):
        msg = self.msg_input.toPlainText().strip()
        if not msg or not self.active_conv_id:
            return
        conv = self._active_conv()
        if not conv:
            return
        provider = self.model_sel.get_provider()
        model = self.model_sel.get_model()
        system = self.system_edit.toPlainText().strip()

        # Update conv metadata
        conv["provider"] = provider
        conv["model"] = model
        conv["system"] = system
        conv["messages"].append({
            "role": "user",
            "content": msg,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        if conv["title"] == "New conversation" and msg:
            conv["title"] = msg[:40]
            self._rebuild_conv_list()

        self.msg_input.clear()
        self._append_user_bubble(msg)

        self._streaming_bubble_id = str(uuid.uuid4())[:8]
        self._stream_t0 = time.time()
        self.send_btn.hide()
        self.stop_btn.show()
        self.status_update.emit(f"Waiting for {provider}/{model}...")

        self.worker = ChatWorker(provider, model, conv["messages"].copy(), system)
        self.worker.token.connect(self._on_token)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

        # Initialise streaming bubble
        self._start_asst_bubble(self._streaming_bubble_id)

    def _on_token(self, token: str):
        self._append_token(token)

    def _on_finished(self, full_text: str, elapsed: float):
        self.stop_btn.hide()
        self.send_btn.show()
        if not self.active_conv_id:
            return
        conv = self._active_conv()
        if not conv:
            return
        bid = self._streaming_bubble_id or str(uuid.uuid4())[:8]
        model = self._stream_model
        conv["messages"].append({
            "role": "assistant",
            "content": full_text,
            "model": model,
            "elapsed": elapsed,
            "bubble_id": bid,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        self._streaming_content = ""
        self._streaming_bubble_id = None
        self._rebuild_html()
        toks = estimate_tokens(full_text)
        self.status_update.emit(f"{model} | {elapsed:.1f}s | ~{toks} tokens")
        self.save_conversations()

    def _on_error(self, err: str):
        self.stop_btn.hide()
        self.send_btn.show()
        self.status_update.emit(f"[!] Error: {err}")

    def _stop_generation(self):
        if self.worker:
            self.worker.stop()
        self.stop_btn.hide()
        self.send_btn.show()

    def _regenerate(self):
        conv = self._active_conv()
        if not conv or not conv["messages"]:
            return
        # Remove last assistant message if present
        if conv["messages"] and conv["messages"][-1]["role"] == "assistant":
            conv["messages"].pop()
        self._rebuild_html()
        if conv["messages"] and conv["messages"][-1]["role"] == "user":
            last_user = conv["messages"].pop()
            self.msg_input.setPlainText(last_user["content"])
            self._send()

    def _clear_chat(self):
        conv = self._active_conv()
        if not conv:
            return
        reply = QMessageBox.question(self, "Clear Chat",
            "Clear all messages in this conversation?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conv["messages"] = []
            conv["title"] = "New conversation"
            self._rebuild_html()
            self._rebuild_conv_list()

    # ---- System prompt ----

    def _toggle_sys_prompt(self):
        self._sys_visible = not self._sys_visible
        self.system_edit.setVisible(self._sys_visible)
        self.sys_toggle_btn.setText("[^] Hide" if self._sys_visible else "[v] Show")

    def _on_preset_changed(self, name: str):
        prompt = SYSTEM_PRESETS.get(name, "")
        if name != "Custom" and prompt:
            self.system_edit.setPlainText(prompt)

    # ---- Input field ----

    def eventFilter(self, obj, event):
        if obj == self.msg_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    def _on_input_changed(self):
        text = self.msg_input.toPlainText()
        toks = estimate_tokens(text) if text.strip() else 0
        ctx = 4096
        if toks == 0:
            color = COLORS['muted']
        else:
            pct = toks / ctx
            if pct < 0.5:
                color = COLORS['green']
            elif pct < 0.8:
                color = COLORS['yellow']
            else:
                color = COLORS['red']
        self.token_lbl.setText(f"{toks} / {ctx} tokens")
        self.token_lbl.setStyleSheet(f"font-size:11px;color:{color};")

    # ---- Export ----

    def _export_conversation(self):
        conv = self._active_conv()
        if not conv:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Conversation", "",
            "Markdown (*.md);;Plain Text (*.txt);;JSON (*.json)")
        if not path:
            return
        try:
            if path.endswith(".json"):
                Path(path).write_text(json.dumps(conv, indent=2))
            elif path.endswith(".md"):
                lines = [f"# {conv['title']}\n"]
                for msg in conv["messages"]:
                    role = "**You**" if msg["role"]=="user" else f"**{msg.get('model','Assistant')}**"
                    lines.append(f"{role}\n\n{msg['content']}\n\n---\n")
                Path(path).write_text("\n".join(lines))
            else:
                lines = []
                for msg in conv["messages"]:
                    role = "You" if msg["role"]=="user" else "Assistant"
                    lines.append(f"[{role}]\n{msg['content']}\n")
                Path(path).write_text("\n".join(lines))
            self.status_update.emit(f"Exported to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))

    def copy_message(self, text: str):
        QApplication.clipboard().setText(text)
        self.status_update.emit("Copied to clipboard.")


# ══════════════════════════════════════════════════════════════════
# TAB: AGENT
# ══════════════════════════════════════════════════════════════════

class AgentTab(QWidget):
    status_update = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[AgentWorker] = None
        self.run_history: List[Dict] = []
        self._setup_ui()
        RUNS_DIR.mkdir(exist_ok=True)

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._main_splitter = QSplitter(Qt.Horizontal)
        self._main_splitter.setHandleWidth(3)
        self._main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {COLORS['border']};
            }}
            QSplitter::handle:hover {{
                background: {COLORS['accent']};
            }}
        """)

        # -- Left: run history --
        sidebar = QWidget()
        sidebar.setStyleSheet(f"background:{COLORS['panel']};")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 12, 10, 12)
        sb_layout.setSpacing(8)

        sb_title = QLabel("Run History")
        sb_title.setStyleSheet(f"font-size:11px;color:{COLORS['muted']};letter-spacing:1px;text-transform:uppercase;font-weight:600;")
        sb_layout.addWidget(sb_title)

        self.history_list = QListWidget()
        self.history_list.currentItemChanged.connect(self._on_history_selected)
        sb_layout.addWidget(self.history_list, stretch=1)

        open_dir_btn = make_button("[ Open Runs Dir ]")
        open_dir_btn.clicked.connect(self._open_runs_dir)
        sb_layout.addWidget(open_dir_btn)

        sidebar.setMinimumWidth(140)
        sidebar.setMaximumWidth(400)
        self._main_splitter.addWidget(sidebar)

        # -- Main --
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        main_layout.addWidget(make_label("Agent", bold=True, size=18, color=COLORS['text']))
        main_layout.addWidget(make_label("Give the agent a goal. It will plan, use tools, and report back.", muted=True))
        main_layout.addWidget(make_divider())

        # Model selector
        self.model_sel = ModelSelector()
        main_layout.addWidget(self.model_sel)

        # System prompt
        sys_lbl = make_label("Agent system prompt:", muted=True)
        main_layout.addWidget(sys_lbl)
        self.system_edit = QTextEdit()
        self.system_edit.setMaximumHeight(56)
        self.system_edit.setPlainText("You are a capable AI agent. Think step by step, use available tools, and solve the goal efficiently.")
        main_layout.addWidget(self.system_edit)

        # Goal + controls
        goal_row = QHBoxLayout()
        goal_row.setSpacing(6)
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("Enter agent goal here...")
        self.goal_input.returnPressed.connect(self._run_agent)
        goal_row.addWidget(self.goal_input, stretch=1)
        BTN_W = 96
        self.run_btn = make_button("[ Run >> ]", "primary")
        self.run_btn.setFixedWidth(BTN_W)
        self.run_btn.clicked.connect(self._run_agent)
        self.stop_btn = make_button("[ Stop ]", "stop")
        self.stop_btn.setFixedWidth(BTN_W)
        self.stop_btn.hide()
        self.stop_btn.clicked.connect(self._stop_agent)
        goal_row.addWidget(self.run_btn)
        goal_row.addWidget(self.stop_btn)
        main_layout.addLayout(goal_row)

        # Tool toggles + iterations
        tools_row = QHBoxLayout()
        tools_row.addWidget(make_label("Tools:", muted=True))
        self.tool_checks: Dict[str, QCheckBox] = {}
        for tool in ["calculator", "web_search", "file_reader"]:
            cb = QCheckBox(tool.replace("_"," ").title())
            cb.setChecked(True)
            self.tool_checks[tool] = cb
            tools_row.addWidget(cb)
        tools_row.addSpacing(16)
        tools_row.addWidget(make_label("Max steps:", muted=True))
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 20)
        self.max_iter_spin.setValue(5)
        self.max_iter_spin.setFixedWidth(60)
        tools_row.addWidget(self.max_iter_spin)
        tools_row.addStretch()
        main_layout.addLayout(tools_row)

        main_layout.addWidget(make_divider())

        # Step log table
        self.step_table = QTableWidget(0, 5)
        self.step_table.setHorizontalHeaderLabels(["Step", "Tool", "Input", "Output", "ms"])
        self.step_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.step_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.step_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.step_table.verticalHeader().setVisible(False)
        self.step_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.step_table, stretch=1)

        # Final answer
        main_layout.addWidget(make_label("Final Answer:", muted=True))
        self.final_display = QTextBrowser()
        self.final_display.setMaximumHeight(120)
        self.final_display.setStyleSheet(f"""
            QTextBrowser {{
                background:{COLORS['surface']};
                border:1px solid {COLORS['border']};
                border-radius:6px;
                padding:10px;
                color:{COLORS['text']};
                font-size:13px;
            }}
        """)
        main_layout.addWidget(self.final_display)

        self._main_splitter.addWidget(main)
        self._main_splitter.setSizes([200, 1100])
        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)
        root.addWidget(self._main_splitter)

    def _run_agent(self):
        goal = self.goal_input.text().strip()
        if not goal:
            return
        provider = self.model_sel.get_provider()
        model = self.model_sel.get_model()
        system = self.system_edit.toPlainText().strip()
        tools_enabled = [k for k, cb in self.tool_checks.items() if cb.isChecked()]
        max_iter = self.max_iter_spin.value()

        self.step_table.setRowCount(0)
        self.final_display.setHtml("")
        self.run_btn.hide()
        self.stop_btn.show()
        self.status_update.emit(f"Agent running on {provider}/{model}...")

        self.worker = AgentWorker(goal, provider, model, system, tools_enabled, max_iter)
        self.worker.step.connect(self._on_step)
        self.worker.finished.connect(self._on_agent_finished)
        self.worker.error.connect(lambda e: self.status_update.emit(f"[!] Agent error: {e}"))
        self.worker.start()

    def _on_step(self, step_data: Dict):
        row = self.step_table.rowCount()
        self.step_table.insertRow(row)
        for col, key in enumerate(["step","tool","input","output","ms"]):
            val = str(step_data.get(key, ""))
            item = QTableWidgetItem(val)
            item.setToolTip(val)
            self.step_table.setItem(row, col, item)
        self.step_table.scrollToBottom()

    def _on_agent_finished(self, final: str):
        self.run_btn.show()
        self.stop_btn.hide()
        self.final_display.setHtml(md_to_html(final))
        self.status_update.emit("Agent finished.")

        # Save run
        goal = self.goal_input.text().strip()
        provider = self.model_sel.get_provider()
        model = self.model_sel.get_model()
        steps = []
        for row in range(self.step_table.rowCount()):
            steps.append({
                "step": self.step_table.item(row,0).text() if self.step_table.item(row,0) else "",
                "tool": self.step_table.item(row,1).text() if self.step_table.item(row,1) else "",
                "input": self.step_table.item(row,2).text() if self.step_table.item(row,2) else "",
                "output": self.step_table.item(row,3).text() if self.step_table.item(row,3) else "",
                "ms": self.step_table.item(row,4).text() if self.step_table.item(row,4) else "",
            })
        run = {
            "goal": goal,
            "provider": provider,
            "model": model,
            "final": final,
            "steps": steps,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.run_history.insert(0, run)
        fname = RUNS_DIR / f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            fname.write_text(json.dumps(run, indent=2))
        except Exception:
            pass
        self._rebuild_history_list()

    def _stop_agent(self):
        if self.worker:
            self.worker.stop()
        self.run_btn.show()
        self.stop_btn.hide()
        self.status_update.emit("Agent stopped.")

    def _rebuild_history_list(self):
        self.history_list.clear()
        for run in self.run_history:
            ts = run.get("timestamp","")[:16].replace("T"," ")
            goal = run.get("goal","")[:28]
            model = run.get("model","")[:18]
            item = QListWidgetItem(f"{goal}\n  {model} | {ts}")
            item.setData(Qt.UserRole, run)
            self.history_list.addItem(item)

    def _on_history_selected(self, current, _previous):
        if not current:
            return
        run = current.data(Qt.UserRole)
        if not run:
            return
        self.goal_input.setText(run.get("goal",""))
        steps = run.get("steps",[])
        self.step_table.setRowCount(0)
        for s in steps:
            row = self.step_table.rowCount()
            self.step_table.insertRow(row)
            for col, key in enumerate(["step","tool","input","output","ms"]):
                self.step_table.setItem(row, col, QTableWidgetItem(str(s.get(key,""))))
        self.final_display.setHtml(md_to_html(run.get("final","")))

    def _open_runs_dir(self):
        import subprocess
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(RUNS_DIR.resolve())])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(RUNS_DIR.resolve())])
            else:
                subprocess.Popen(["xdg-open", str(RUNS_DIR.resolve())])
        except Exception as e:
            self.status_update.emit(f"[!] Cannot open directory: {e}")


# ══════════════════════════════════════════════════════════════════
# TAB: SETTINGS
# ══════════════════════════════════════════════════════════════════

class SettingsTab(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._refresh_health)
        self._health_timer.start(30000)
        self._setup_ui()
        self._refresh_health()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        layout.addWidget(make_label("Settings", bold=True, size=18, color=COLORS['text']))
        layout.addWidget(make_label("API keys, appearance, and data management.", muted=True))
        layout.addWidget(make_divider())

        # -- API Keys --
        keys_group = QGroupBox("API Keys")
        keys_layout = QVBoxLayout(keys_group)
        self.key_fields: Dict[str, QLineEdit] = {}
        for label, key in [
            ("Groq API Key", "groq_key"),
            ("Anthropic API Key", "anthropic_key"),
            ("Gemini API Key", "gemini_key"),
            ("NIM API Key", "nim_key"),
            ("NIM Base URL", "nim_base"),
            ("Ollama Base URL", "ollama_base"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setFixedWidth(160)
            lbl.setStyleSheet(f"color:{COLORS['text']};font-size:12px;")
            row.addWidget(lbl)
            field = QLineEdit(S(key,""))
            if "key" in key.lower() and key != "ollama_base" and key != "nim_base":
                field.setEchoMode(QLineEdit.Password)
            self.key_fields[key] = field
            row.addWidget(field)
            keys_layout.addLayout(row)

        save_btn = make_button("[ Save Settings ]", "primary")
        save_btn.clicked.connect(self._save_settings)
        keys_layout.addWidget(save_btn)
        layout.addWidget(keys_group)

        # -- Provider Health --
        health_group = QGroupBox("Provider Health  (auto-refresh every 30s)")
        self.health_layout = QVBoxLayout(health_group)
        self.health_labels: Dict[str, QLabel] = {}
        for provider in PROVIDERS:
            row = QHBoxLayout()
            status_lbl = QLabel("[?]")
            status_lbl.setFixedWidth(32)
            status_lbl.setStyleSheet(f"color:{COLORS['muted']};font-family:monospace;font-weight:700;")
            self.health_labels[provider] = status_lbl
            row.addWidget(status_lbl)
            name_lbl = QLabel(PROVIDERS[provider]["label"])
            name_lbl.setStyleSheet(f"color:{COLORS['text']};font-size:12px;")
            row.addWidget(name_lbl)
            row.addStretch()
            self.health_layout.addLayout(row)

        refresh_btn = make_button("[~] Refresh Now")
        refresh_btn.clicked.connect(self._refresh_health)
        self.health_layout.addWidget(refresh_btn)
        layout.addWidget(health_group)

        # -- Appearance --
        appear_group = QGroupBox("Appearance")
        appear_layout = QVBoxLayout(appear_group)

        font_row = QHBoxLayout()
        font_row.addWidget(make_label("Font size:", muted=True))
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(11, 18)
        self.font_slider.setValue(S("font_size", 13))
        self.font_lbl = make_label(f"{S('font_size',13)}px", muted=True)
        self.font_slider.valueChanged.connect(lambda v: self.font_lbl.setText(f"{v}px"))
        font_row.addWidget(self.font_slider)
        font_row.addWidget(self.font_lbl)
        appear_layout.addLayout(font_row)

        accent_row = QHBoxLayout()
        accent_row.addWidget(make_label("Accent colour:", muted=True))
        self.accent_btns: Dict[str, QPushButton] = {}
        for color in ["#4f8ef7","#7c3aed","#22d3a5","#f59e0b","#ef4444","#e879f9"]:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"background:{color};border-radius:12px;border:2px solid {COLORS['border']};")
            btn.clicked.connect(lambda checked, c=color: self._set_accent(c))
            accent_row.addWidget(btn)
            self.accent_btns[color] = btn
        accent_row.addStretch()
        appear_layout.addLayout(accent_row)

        apply_appear_btn = make_button("[ Apply Appearance ]", "primary")
        apply_appear_btn.clicked.connect(self._apply_appearance)
        appear_layout.addWidget(apply_appear_btn)
        layout.addWidget(appear_group)

        # -- Default Prompt --
        prompt_group = QGroupBox("Default System Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        self.default_prompt_edit = QTextEdit()
        self.default_prompt_edit.setMaximumHeight(80)
        self.default_prompt_edit.setPlainText(S("default_system",""))
        prompt_layout.addWidget(self.default_prompt_edit)
        layout.addWidget(prompt_group)

        # -- Data --
        data_group = QGroupBox("Data")
        data_layout = QHBoxLayout(data_group)
        exp_btn = make_button("[ Export All Convs ]")
        exp_btn.clicked.connect(self._export_all)
        clr_btn = make_button("[ Clear All Convs ]", "danger")
        clr_btn.clicked.connect(self._clear_all)
        data_layout.addWidget(exp_btn)
        data_layout.addWidget(clr_btn)
        data_layout.addStretch()
        layout.addWidget(data_group)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._pending_accent = S("accent", COLORS['accent'])

    def _save_settings(self):
        s = dict(_settings)
        for key, field in self.key_fields.items():
            s[key] = field.text().strip()
        s["default_system"] = self.default_prompt_edit.toPlainText().strip()
        s["font_size"] = self.font_slider.value()
        s["accent"] = self._pending_accent
        save_settings(s)
        self.settings_changed.emit(s)

    def _apply_appearance(self):
        self._save_settings()

    def _set_accent(self, color: str):
        self._pending_accent = color
        for c, btn in self.accent_btns.items():
            border = COLORS['text'] if c == color else COLORS['border']
            btn.setStyleSheet(f"background:{c};border-radius:12px;border:2px solid {border};")

    def _refresh_health(self):
        for provider, lbl in self.health_labels.items():
            status, color = self._check_provider(provider)
            lbl.setText(status)
            lbl.setStyleSheet(f"color:{color};font-family:monospace;font-weight:700;")

    def _check_provider(self, provider: str):
        if provider == "ollama":
            base = S("ollama_base","http://localhost:11434")
            try:
                with urllib.request.urlopen(f"{base}/api/tags", timeout=2) as r:
                    data = json.loads(r.read())
                count = len(data.get("models",[]))
                return f"[+] {count} models", COLORS['green']
            except Exception:
                return "[!] not running", COLORS['red']
        elif provider == "nim":
            key = S("nim_key","")
            if key:
                return "[+] key set", COLORS['green']
            return "[?] no key", COLORS['muted']
        elif provider == "groq":
            key = S("groq_key","") or os.environ.get("GROQ_API_KEY","")
            if key:
                return "[+] key set", COLORS['green']
            return "[?] no key", COLORS['muted']
        elif provider == "anthropic":
            key = S("anthropic_key","") or os.environ.get("ANTHROPIC_API_KEY","")
            if key:
                return "[+] key set", COLORS['green']
            return "[?] no key", COLORS['muted']
        elif provider == "gemini":
            key = S("gemini_key","") or os.environ.get("GEMINI_API_KEY","")
            if key:
                return "[+] key set", COLORS['green']
            return "[?] no key", COLORS['muted']
        return "[?]", COLORS['muted']

    def _export_all(self):
        if not CONVERSATIONS_FILE.exists():
            QMessageBox.information(self, "Export", "No conversations to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export All Conversations", "conversations.json", "JSON (*.json)")
        if path:
            try:
                import shutil
                shutil.copy(CONVERSATIONS_FILE, path)
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _clear_all(self):
        reply = QMessageBox.question(self, "Clear All",
            "Delete ALL conversations permanently?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if CONVERSATIONS_FILE.exists():
                CONVERSATIONS_FILE.unlink()


# ══════════════════════════════════════════════════════════════════
# EMBEDDED TERMINAL (improved)
# ══════════════════════════════════════════════════════════════════
#
# Improvements over the sf.py terminal:
#   - Persistent history saved to ~/.sfm_term_history
#   - Up/Down arrow navigation + Ctrl+L to clear
#   - Built-ins: cd, pwd, clear, help, history, ask
#   - "ask <question>" pipes the question to the active chat provider/model
#     and prints the reply directly in the terminal (no tab switch needed)
#   - ANSI escape stripping so colored CLI output renders cleanly
#   - No emoji anywhere -- uses ">>" as the prompt, "[+]" / "[!]" markers
#   - Collapsible via a toggle button in the title bar
#   - Run-external API so other tabs can push commands into it

TERM_HISTORY_FILE = Path.home() / ".sfm_term_history"

class TerminalAskWorker(QThread):
    """Background worker that asks the chat model a question from the terminal."""
    reply = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, provider, model, system, question, tag: str = "ask"):
        super().__init__()
        self.provider = provider
        self.model = model
        self.system = system
        self.question = question
        self.tag = tag  # so the UI can route the reply (explain/why/fix/etc)

    def run(self):
        try:
            result = call_provider(
                self.provider, self.model,
                [{"role": "user", "content": self.question}],
                self.system
            )
            self.reply.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class EmbeddedTerminal(QWidget):
    """An embedded terminal that runs shell commands AND can ask the chat model."""

    TERM_BG   = "#080a0f"
    TERM_TEXT = "#00ff88"
    TERM_DIM  = "#3a5a3a"
    TERM_ERR  = "#ff6464"
    TERM_INFO = "#64a0ff"

    # Provider for "ask" command -- set externally by MainWindow so it
    # mirrors whatever the Chat tab currently has selected.
    ask_provider = "ollama"
    ask_model = ""
    ask_system = "You are a concise terminal assistant. Reply in plain text."

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process: Optional[QProcess] = None
        self.history: List[str] = self._load_history()
        self.history_idx = len(self.history)
        self.cwd = Path.cwd()
        self._collapsed = False
        self._ask_worker: Optional[TerminalAskWorker] = None
        # State for new commands
        self._last_cmd: str = ""                 # for !! and undo
        self._last_output: List[str] = []        # for why, copy, send-to-chat
        self._last_exit: int = 0                 # for fix
        self._pending_confirm: Optional[str] = None  # for run/undo confirmation
        self._teach_mode: bool = False           # toggled by `teach on`/`teach off`
        self._aliases: Dict[str, str] = self._load_aliases()
        self._setup_ui()
        self._welcome()

    # ---- Aliases ----

    @staticmethod
    def _aliases_path() -> Path:
        return Path.home() / ".sfm_term_aliases.json"

    def _load_aliases(self) -> Dict[str, str]:
        p = self._aliases_path()
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                return {}
        return {}

    def _save_aliases(self):
        try:
            self._aliases_path().write_text(json.dumps(self._aliases, indent=2))
        except Exception:
            pass

    # ---- Persistent history ----

    def _load_history(self) -> List[str]:
        if TERM_HISTORY_FILE.exists():
            try:
                return [l.rstrip("\n") for l in TERM_HISTORY_FILE.read_text().splitlines() if l.strip()][-500:]
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            TERM_HISTORY_FILE.write_text("\n".join(self.history[-500:]))
        except Exception:
            pass

    # ---- UI ----

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(28)
        title_bar.setStyleSheet(f"""
            background: {self.TERM_BG};
            border: 1px solid #1a2a1a;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        """)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(10, 4, 8, 4)
        tb.setSpacing(8)

        # ASCII dots (no unicode)
        for color in ["#ff5f57", "#febc2e", "#28c840"]:
            d = QLabel("*")
            d.setStyleSheet(f"color:{color};font-size:14px;font-weight:700;")
            tb.addWidget(d)

        tb.addSpacing(6)
        title_lbl = QLabel("terminal")
        title_lbl.setStyleSheet(f"color:{COLORS['muted']};font-size:11px;font-family:monospace;")
        tb.addWidget(title_lbl)

        self.cwd_lbl = QLabel(self._short_cwd())
        self.cwd_lbl.setStyleSheet(f"color:{self.TERM_DIM};font-size:11px;font-family:monospace;")
        tb.addWidget(self.cwd_lbl)
        tb.addStretch()

        # Title-bar buttons
        for label, slot in [("clear", self.clear_output),
                            ("help",  self._show_help),
                            ("[-]",   self._toggle_collapse)]:
            btn = QPushButton(label)
            btn.setFixedHeight(20)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['muted']};
                    border: none;
                    font-size: 11px;
                    font-family: monospace;
                    padding: 0 8px;
                }}
                QPushButton:hover {{ color: {self.TERM_TEXT}; }}
            """)
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        layout.addWidget(title_bar)

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.TERM_BG};
                color: {self.TERM_TEXT};
                border: 1px solid #1a2a1a;
                border-top: none;
                border-bottom: none;
                border-radius: 0;
                padding: 8px 10px;
                font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                selection-background-color: #1a4a1a;
            }}
        """)
        self.output.setMinimumHeight(160)
        layout.addWidget(self.output, stretch=1)

        # Input row
        input_row = QWidget()
        input_row.setStyleSheet(f"""
            background: {self.TERM_BG};
            border: 1px solid #1a2a1a;
            border-top: none;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
        """)
        ir = QHBoxLayout(input_row)
        ir.setContentsMargins(10, 4, 10, 6)
        ir.setSpacing(8)

        self.prompt_lbl = QLabel(">>")
        self.prompt_lbl.setStyleSheet(f"color:{self.TERM_TEXT};font-family:monospace;font-size:13px;font-weight:700;")
        ir.addWidget(self.prompt_lbl)

        self.cmd_input = QLineEdit()
        self.cmd_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {self.TERM_TEXT};
                border: none;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 12px;
                padding: 2px 0;
            }}
        """)
        self.cmd_input.setPlaceholderText("type a shell command, or 'ask <question>' to query the model, or 'help'")
        self.cmd_input.returnPressed.connect(self._run_command)
        self.cmd_input.installEventFilter(self)
        ir.addWidget(self.cmd_input)

        layout.addWidget(input_row)

        self._input_row = input_row

    def _short_cwd(self) -> str:
        try:
            home = str(Path.home())
            s = str(self.cwd)
            if s.startswith(home):
                s = "~" + s[len(home):]
            if len(s) > 50:
                s = "..." + s[-47:]
            return s
        except Exception:
            return str(self.cwd)

    def _welcome(self):
        self._print("sfm terminal -- type 'help' for the full command list", self.TERM_DIM)
        self._print("try: ask, explain, fix, run, risk, undo, why, teach on", self.TERM_DIM)
        self._print(f"cwd: {self.cwd}", self.TERM_DIM)
        self._print("")

    # ---- Output helpers ----

    @staticmethod
    def _strip_ansi(text: str) -> str:
        import re
        return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

    def _print(self, text: str, color: Optional[str] = None):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color or self.TERM_TEXT))
        cursor.setCharFormat(fmt)
        cursor.insertText(self._strip_ansi(text) + "\n")
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def clear_output(self):
        self.output.clear()

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self.output.setVisible(not self._collapsed)
        self._input_row.setVisible(not self._collapsed)

    # ---- Built-ins ----

    def _show_help(self):
        lines = [
            "built-in commands:",
            "  cd <path>           -- change directory",
            "  pwd                 -- show current directory",
            "  clear / cls         -- clear output (or Ctrl+L)",
            "  history             -- show recent commands",
            "  help                -- this message",
            "",
            "AI-assisted commands (uses your active Chat-tab model):",
            "  ask <question>      -- ask the model anything",
            "  explain <cmd>       -- explain what a command will do BEFORE running",
            "  why                 -- explain what just happened (last command output)",
            "  fix                 -- analyze the last failed command and suggest fix",
            "  run <description>   -- describe what you want, model writes the command",
            "  risk <cmd>          -- rate command danger 1-5 before running",
            "  undo                -- generate reverse of last command (with confirm)",
            "  teach on / off      -- toggle: model adds a tip after every command",
            "",
            "shortcuts:",
            "  !!                  -- repeat last command",
            "  time <cmd>          -- run command and show elapsed time",
            "  alias <name>=<cmd>  -- save a shortcut (persists across sessions)",
            "  alias               -- list all saved aliases",
            "  unalias <name>      -- remove an alias",
            "",
            "anything else runs via the system shell.",
            "Up/Down arrows navigate history.",
            "",
        ]
        for ln in lines:
            self._print(ln, self.TERM_INFO)

    # ---- Event filter for history nav + Ctrl+L ----

    def eventFilter(self, obj, event):
        if obj == self.cmd_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                if self.history and self.history_idx > 0:
                    self.history_idx -= 1
                    self.cmd_input.setText(self.history[self.history_idx])
                return True
            if event.key() == Qt.Key_Down:
                if self.history_idx < len(self.history) - 1:
                    self.history_idx += 1
                    self.cmd_input.setText(self.history[self.history_idx])
                else:
                    self.history_idx = len(self.history)
                    self.cmd_input.clear()
                return True
            if event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
                self.clear_output()
                return True
        return super().eventFilter(obj, event)

    # ---- Command dispatch ----

    def _run_command(self):
        cmd_raw = self.cmd_input.text().strip()
        if not cmd_raw:
            return

        # Handle confirmation prompt (y/n for run/undo)
        if self._pending_confirm is not None:
            self.cmd_input.clear()
            confirm = cmd_raw.lower()
            if confirm in ("y", "yes"):
                to_run = self._pending_confirm
                self._pending_confirm = None
                self._print(f">> {to_run}", self.TERM_TEXT)
                self._execute_shell(to_run)
                return
            else:
                self._print("  cancelled", self.TERM_DIM)
                self._pending_confirm = None
                self._print("")
                return

        cmd = cmd_raw
        self.cmd_input.clear()

        # Alias expansion (first token only)
        first = cmd.split(maxsplit=1)[0]
        if first in self._aliases and not cmd.startswith("alias"):
            rest = cmd[len(first):].strip()
            cmd = (self._aliases[first] + " " + rest).strip()
            self._print(f">> {cmd_raw}   [alias -> {cmd}]", self.TERM_TEXT)
        else:
            self._print(f">> {cmd_raw}", self.TERM_TEXT)

        # Don't record the bang command itself; record what it expands to
        if cmd_raw != "!!":
            self.history.append(cmd_raw)
            self.history_idx = len(self.history)
            self._save_history()

        # ---- BUILT-IN COMMANDS ----

        # Basic shell built-ins
        if cmd in ("clear", "cls"):
            self.clear_output()
            return
        if cmd == "help":
            self._show_help()
            return
        if cmd == "pwd":
            self._print(str(self.cwd))
            return
        if cmd == "history":
            for i, h in enumerate(self.history[-30:], 1):
                self._print(f"  {i:3d}  {h}", self.TERM_DIM)
            return
        if cmd.startswith("cd"):
            parts = cmd.split(maxsplit=1)
            target = parts[1].strip() if len(parts) > 1 else str(Path.home())
            try:
                if target == "~":
                    new_path = Path.home()
                else:
                    new_path = (self.cwd / target).expanduser().resolve()
                if not new_path.is_dir():
                    raise NotADirectoryError(str(new_path))
                os.chdir(new_path)
                self.cwd = new_path
                self.cwd_lbl.setText(self._short_cwd())
                self._print(f"  -> {self.cwd}", self.TERM_DIM)
            except Exception as e:
                self._print(f"  cd: {e}", self.TERM_ERR)
            return

        # !! -- repeat last command
        if cmd == "!!":
            if not self._last_cmd:
                self._print("  [!] no previous command to repeat", self.TERM_ERR)
                return
            self._print(f">> {self._last_cmd}", self.TERM_TEXT)
            self._execute_shell(self._last_cmd)
            return

        # time <cmd> -- run a command and report elapsed time
        if cmd.startswith("time "):
            inner = cmd[5:].strip()
            if not inner:
                self._print("  [!] time: provide a command", self.TERM_ERR)
                return
            self._time_start = time.time()
            self._execute_shell(inner, timed=True)
            return

        # alias management
        if cmd == "alias":
            if not self._aliases:
                self._print("  no aliases defined", self.TERM_DIM)
            else:
                for k, v in self._aliases.items():
                    self._print(f"  {k} = {v}", self.TERM_INFO)
            return
        if cmd.startswith("alias "):
            rest = cmd[6:].strip()
            if "=" not in rest:
                self._print("  [!] usage: alias name=command", self.TERM_ERR)
                return
            name, value = rest.split("=", 1)
            name, value = name.strip(), value.strip()
            if not name or not value:
                self._print("  [!] usage: alias name=command", self.TERM_ERR)
                return
            self._aliases[name] = value
            self._save_aliases()
            self._print(f"  alias saved: {name} -> {value}", self.TERM_INFO)
            return
        if cmd.startswith("unalias "):
            name = cmd[8:].strip()
            if name in self._aliases:
                del self._aliases[name]
                self._save_aliases()
                self._print(f"  removed alias: {name}", self.TERM_INFO)
            else:
                self._print(f"  [!] no such alias: {name}", self.TERM_ERR)
            return

        # ---- AI-ASSISTED COMMANDS ----

        if cmd.startswith("ask "):
            question = cmd[4:].strip()
            if not question:
                self._print("  [!] ask: provide a question", self.TERM_ERR)
                return
            self._ask_model(question)
            return

        if cmd.startswith("explain "):
            target = cmd[8:].strip()
            if not target:
                self._print("  [!] explain: provide a command to explain", self.TERM_ERR)
                return
            sys_prompt = (
                "You are a terminal command explainer. Given a shell command, "
                "explain in 2-3 short sentences what it does, what it changes "
                "on the system, and any side effects. Plain text. No code blocks."
            )
            self._ai_query(f"Explain this command: {target}", sys_prompt, tag="explain")
            return

        if cmd == "why":
            if not self._last_output:
                self._print("  [!] no previous output to analyze", self.TERM_ERR)
                return
            out = "\n".join(self._last_output[-40:])
            sys_prompt = (
                "You analyze shell command output. Given the command and its "
                "output, explain in 2-3 sentences what happened and why. "
                "Be concrete. Plain text."
            )
            self._ai_query(
                f"Command: {self._last_cmd}\nExit code: {self._last_exit}\nOutput:\n{out}\n\nWhy did this happen?",
                sys_prompt, tag="why"
            )
            return

        if cmd == "fix":
            if not self._last_cmd:
                self._print("  [!] no previous command to fix", self.TERM_ERR)
                return
            if self._last_exit == 0:
                self._print("  [!] last command succeeded -- nothing to fix", self.TERM_INFO)
                return
            out = "\n".join(self._last_output[-30:])
            sys_prompt = (
                "You diagnose failed shell commands. Given a command and its "
                "error output, give: (1) one-line diagnosis, (2) suggested "
                "corrected command on its own line. Plain text. Be specific."
            )
            self._ai_query(
                f"Failed command: {self._last_cmd}\nExit code: {self._last_exit}\nError output:\n{out}",
                sys_prompt, tag="fix"
            )
            return

        if cmd.startswith("run "):
            desc = cmd[4:].strip()
            if not desc:
                self._print("  [!] run: describe what you want", self.TERM_ERR)
                return
            shell_name = "cmd.exe (Windows)" if sys.platform == "win32" else "bash"
            sys_prompt = (
                f"You convert natural-language requests into a single {shell_name} "
                "command. Output ONLY the command, no explanation, no code fences, "
                "no markdown. One line. Safe and minimal."
            )
            self._ai_query(desc, sys_prompt, tag="run")
            return

        if cmd.startswith("risk "):
            target = cmd[5:].strip()
            if not target:
                self._print("  [!] risk: provide a command to assess", self.TERM_ERR)
                return
            sys_prompt = (
                "You rate the danger of shell commands. Given a command, respond "
                "in this exact format on three lines:\n"
                "RISK: X/5\nIMPACT: <one short sentence>\nREVERSIBLE: yes/no\n"
                "Scale: 1=safe read-only, 2=local writes, 3=could lose work, "
                "4=could break system, 5=catastrophic/irreversible."
            )
            self._ai_query(f"Rate the risk of: {target}", sys_prompt, tag="risk")
            return

        if cmd == "undo":
            if not self._last_cmd:
                self._print("  [!] no previous command to undo", self.TERM_ERR)
                return
            shell_name = "cmd.exe (Windows)" if sys.platform == "win32" else "bash"
            sys_prompt = (
                f"You generate {shell_name} commands that reverse the effect of a "
                "previous command. Output ONLY the reverse command, no explanation, "
                "no markdown. If reversing is impossible (e.g., file already deleted "
                "without backup), output exactly: IMPOSSIBLE"
            )
            self._ai_query(f"Reverse this command: {self._last_cmd}", sys_prompt, tag="undo")
            return

        if cmd == "teach on":
            self._teach_mode = True
            self._print("  teach mode ON -- model will add a tip after each command", self.TERM_INFO)
            return
        if cmd == "teach off":
            self._teach_mode = False
            self._print("  teach mode OFF", self.TERM_INFO)
            return
        if cmd == "teach":
            state = "ON" if self._teach_mode else "OFF"
            self._print(f"  teach mode is {state} -- use 'teach on' or 'teach off'", self.TERM_INFO)
            return

        # ---- EXTERNAL SHELL ----
        self._execute_shell(cmd)

    def _execute_shell(self, cmd: str, timed: bool = False):
        """Run an external shell command, capturing output for state."""
        self._last_cmd = cmd
        self._last_output = []
        self._timed = timed

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.setWorkingDirectory(str(self.cwd))
        self.process.readyReadStandardOutput.connect(self._on_output)
        self.process.finished.connect(self._on_finished)

        try:
            if sys.platform == "win32":
                self.process.start("cmd.exe", ["/c", cmd])
            else:
                self.process.start("bash", ["-lc", cmd])
        except Exception as e:
            self._print(f"  [!] failed to start: {e}", self.TERM_ERR)

    def _ai_query(self, prompt: str, system: str, tag: str = "ask"):
        """Generic AI query routed through the active Chat-tab provider/model."""
        if not self.ask_model:
            self._print("  [!] no model selected -- pick one in the Chat tab first", self.TERM_ERR)
            return
        marker = {
            "ask":     "[?] asking",
            "explain": "[?] explaining",
            "why":     "[?] analyzing output",
            "fix":     "[?] diagnosing failure",
            "run":     "[?] writing command",
            "risk":    "[?] assessing risk",
            "undo":    "[?] reversing command",
            "teach":   "[?] generating tip",
        }.get(tag, "[?] thinking")
        self._print(f"  {marker} via {self.ask_provider}/{self.ask_model}...", self.TERM_INFO)
        self._ask_worker = TerminalAskWorker(
            self.ask_provider, self.ask_model, system, prompt, tag=tag
        )
        self._ask_worker.reply.connect(lambda text: self._on_ai_reply(text, tag))
        self._ask_worker.error.connect(lambda e: self._print(f"  [!] {e}", self.TERM_ERR))
        self._ask_worker.start()

    def _ask_model(self, question: str):
        """Legacy entry point used by the plain `ask` command."""
        self._ai_query(question, self.ask_system, tag="ask")

    def _on_ai_reply(self, text: str, tag: str):
        # For run/undo we expect a single shell command and prompt to confirm
        if tag in ("run", "undo"):
            suggested = self._extract_command(text)
            if not suggested:
                self._print("  [!] model did not return a usable command:", self.TERM_ERR)
                for line in text.splitlines():
                    self._print(f"  {line}", self.TERM_INFO)
                self._print("")
                return
            self._pending_confirm = suggested
            self._print(f"  suggested: {suggested}", self.TERM_INFO)
            self._print("  type 'y' to run, anything else to cancel", self.TERM_DIM)
            self._print("")
            return

        # Default: just print the reply
        for line in text.splitlines():
            self._print(f"  {line}", self.TERM_INFO)
        self._print("")

    @staticmethod
    def _extract_command(text: str) -> str:
        """Pull a clean shell command out of the model's reply.
        Looks for fenced code blocks first, then the first non-empty line."""
        import re
        # Fenced code block
        m = re.search(r"```(?:\w+)?\n?(.*?)```", text, flags=re.DOTALL)
        if m:
            block = m.group(1).strip()
            # Take the first non-empty line of the block
            for line in block.splitlines():
                if line.strip():
                    return line.strip()
        # Backtick inline
        m = re.search(r"`([^`\n]+)`", text)
        if m:
            return m.group(1).strip()
        # First non-empty line
        for line in text.splitlines():
            ls = line.strip()
            if ls and not ls.startswith(("[", "#", "//")):
                return ls
        return ""

    def _on_output(self):
        if not self.process:
            return
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            self._last_output.append(line)
            self._print(line)

    def _on_finished(self, exit_code, _exit_status):
        self._last_exit = exit_code
        if getattr(self, "_timed", False):
            elapsed = time.time() - getattr(self, "_time_start", time.time())
            self._print(f"  [elapsed: {elapsed:.2f}s]", self.TERM_INFO)
            self._timed = False
        if exit_code != 0:
            self._print(f"  [exit {exit_code}]", self.TERM_ERR)
        self._print("")

        # Teach mode: model offers a tip after each command
        if self._teach_mode and self._last_cmd and self.ask_model:
            sys_prompt = (
                "You are a concise terminal tutor. Given a command that was just "
                "run, share ONE short tip the user might not know -- a flag, a "
                "shortcut, a better alternative, or a related command. One line. "
                "Start with 'tip:'. No code blocks."
            )
            self._ai_query(
                f"Command just run: {self._last_cmd}",
                sys_prompt, tag="teach"
            )

    # ---- Public API ----

    def run_cmd_external(self, cmd: str):
        """Called by other tabs to inject a command."""
        self.cmd_input.setText(cmd)
        self._run_command()

    def set_ask_target(self, provider: str, model: str):
        """Wire the 'ask' built-in to whatever the Chat tab currently has selected."""
        self.ask_provider = provider
        self.ask_model = model


# ══════════════════════════════════════════════════════════════════
# TERMINAL PANE -- holds multiple terminals with a small tab bar
# ══════════════════════════════════════════════════════════════════

class TerminalPane(QWidget):
    """Container that hosts one or more EmbeddedTerminal instances and lets
    you switch between them with a small tab strip across the top. Each
    terminal keeps its own cwd, history, output, and command state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._terminals: List[EmbeddedTerminal] = []
        self._tab_buttons: List[QPushButton] = []
        self._active_idx: int = 0
        self._ask_provider: str = "ollama"
        self._ask_model: str = ""
        self._setup_ui()
        self.add_terminal()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Mini tab strip
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(26)
        self._tab_bar.setStyleSheet(f"""
            background: {COLORS['panel']};
            border-top: 1px solid {COLORS['border']};
            border-left: 1px solid {COLORS['border']};
            border-right: 1px solid {COLORS['border']};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        """)
        self._tab_layout = QHBoxLayout(self._tab_bar)
        self._tab_layout.setContentsMargins(6, 3, 6, 0)
        self._tab_layout.setSpacing(2)
        self._tab_layout.addStretch()
        layout.addWidget(self._tab_bar)

        # Stack holding the terminals
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, stretch=1)

    def _make_tab_button(self, idx: int, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setFixedHeight(22)
        btn.setMinimumWidth(80)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['surface']};
                color: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 2px 12px;
                font-size: 11px;
                font-family: monospace;
            }}
            QPushButton:checked {{
                background: #080a0f;
                color: #00ff88;
                border-color: #1a2a1a;
            }}
            QPushButton:hover:!checked {{
                color: {COLORS['text']};
            }}
        """)
        btn.clicked.connect(lambda: self._switch_to(idx))
        return btn

    def _refresh_tab_bar(self):
        # Clear out and rebuild
        for i in reversed(range(self._tab_layout.count())):
            item = self._tab_layout.itemAt(i)
            w = item.widget()
            if w:
                w.deleteLater()
            else:
                self._tab_layout.removeItem(item)

        self._tab_buttons = []
        for i, term in enumerate(self._terminals):
            btn = self._make_tab_button(i, f"term {i+1}")
            btn.setChecked(i == self._active_idx)
            self._tab_layout.addWidget(btn)
            self._tab_buttons.append(btn)

        # New-terminal and close buttons
        add_btn = QPushButton("[+]")
        add_btn.setFixedHeight(22)
        add_btn.setFixedWidth(28)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['muted']};
                border: none;
                font-family: monospace;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: {COLORS['accent']}; }}
        """)
        add_btn.setToolTip("New terminal")
        add_btn.clicked.connect(self.add_terminal)
        self._tab_layout.addWidget(add_btn)

        if len(self._terminals) > 1:
            close_btn = QPushButton("[x]")
            close_btn.setFixedHeight(22)
            close_btn.setFixedWidth(28)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['muted']};
                    border: none;
                    font-family: monospace;
                    font-size: 11px;
                }}
                QPushButton:hover {{ color: {COLORS['red']}; }}
            """)
            close_btn.setToolTip("Close active terminal")
            close_btn.clicked.connect(self.close_active_terminal)
            self._tab_layout.addWidget(close_btn)

        self._tab_layout.addStretch()

    def add_terminal(self):
        term = EmbeddedTerminal()
        term.set_ask_target(self._ask_provider, self._ask_model)
        self._terminals.append(term)
        self._stack.addWidget(term)
        self._active_idx = len(self._terminals) - 1
        self._stack.setCurrentIndex(self._active_idx)
        self._refresh_tab_bar()

    def close_active_terminal(self):
        if len(self._terminals) <= 1:
            return
        idx = self._active_idx
        term = self._terminals.pop(idx)
        self._stack.removeWidget(term)
        term.deleteLater()
        self._active_idx = max(0, idx - 1)
        self._stack.setCurrentIndex(self._active_idx)
        self._refresh_tab_bar()

    def _switch_to(self, idx: int):
        if 0 <= idx < len(self._terminals):
            self._active_idx = idx
            self._stack.setCurrentIndex(idx)
            for i, btn in enumerate(self._tab_buttons):
                btn.setChecked(i == idx)

    def set_ask_target(self, provider: str, model: str):
        """Push the active model down to every terminal so all 'ask' commands stay synced."""
        self._ask_provider = provider
        self._ask_model = model
        for term in self._terminals:
            term.set_ask_target(provider, model)

    def active_terminal(self) -> Optional[EmbeddedTerminal]:
        if self._terminals:
            return self._terminals[self._active_idx]
        return None


# ══════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ══════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SupportLabs  --  sfm")
        self.setMinimumSize(1280, 800)
        self.resize(1440, 880)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet(f"background:{COLORS['panel']};border-bottom:1px solid {COLORS['border']};")
        title_bar.setFixedHeight(46)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(18, 0, 14, 0)
        tb_layout.setSpacing(8)

        logo = QLabel("SupportLabs")
        logo.setStyleSheet(f"font-size:16px;font-weight:700;color:{COLORS['accent']};letter-spacing:-0.5px;")
        tb_layout.addWidget(logo)

        sep = QLabel("sfm")
        sep.setStyleSheet(f"font-size:12px;color:{COLORS['muted']};padding:2px 8px;border:1px solid {COLORS['border']};border-radius:4px;")
        tb_layout.addWidget(sep)
        tb_layout.addStretch()

        # Subtle keyboard hint, nudges users to discover shortcuts
        hint = QLabel("Ctrl+N  new  ::  Ctrl+/  focus  ::  F11  zen")
        hint.setStyleSheet(f"font-size:10px;color:{COLORS['muted']};font-family:monospace;opacity:0.7;")
        tb_layout.addWidget(hint)

        tb_layout.addSpacing(10)
        self.header_status = QLabel("Ready")
        self.header_status.setStyleSheet(f"font-size:11px;color:{COLORS['muted']};")
        tb_layout.addWidget(self.header_status)

        tb_layout.addSpacing(10)
        self.term_toggle_btn = QPushButton("[ Terminal ]")
        self.term_toggle_btn.setCheckable(True)
        self.term_toggle_btn.setChecked(True)
        self.term_toggle_btn.setFixedWidth(110)
        self.term_toggle_btn.clicked.connect(self._toggle_terminal)
        tb_layout.addWidget(self.term_toggle_btn)
        root.addWidget(title_bar)

        # Tabs + terminal in a vertical splitter
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Only create Chat tab immediately (it's the default)
        self.chat_tab = ChatTab()
        self.agent_tab = None
        self.settings_tab = None
        
        self.tabs.addTab(self.chat_tab, "Chat")
        self.tabs.addTab(QWidget(), "Agent")      # Placeholder
        self.tabs.addTab(QWidget(), "Settings")   # Placeholder
        
        self.terminal = TerminalPane()

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {COLORS['border']};
                height: 4px;
            }}
            QSplitter::handle:hover {{
                background: {COLORS['accent']};
            }}
        """)
        self.splitter.addWidget(self.tabs)
        self.splitter.addWidget(self.terminal)
        self.splitter.setSizes([620, 220])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        root.addWidget(self.splitter, stretch=1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("sfm ready  --  See Settings to configure API keys")

        # Wire status signals (only Chat now, others lazy-load)
        self.chat_tab.status_update.connect(self._on_status)
        # agent_tab and settings_tab will be connected when they're created

        # Sync terminal "ask" target with whichever model the Chat tab has
        # selected. Update on initial load and whenever the model changes.
        self.chat_tab.model_sel.model_changed.connect(self._sync_terminal_ask_target)
        self._sync_terminal_ask_target(
            self.chat_tab.model_sel.get_provider(),
            self.chat_tab.model_sel.get_model()
        )

        # Metrics auto-refresh
        self._metrics_timer = QTimer(self)
        self._metrics_timer.timeout.connect(self._refresh_metrics)
        self._metrics_timer.start(10000)

        # Keyboard shortcuts -- the small things that make an app feel alive
        self._focus_mode = False
        self._saved_chat_sizes = None
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._shortcut_new_chat)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self._shortcut_clear_input)
        QShortcut(QKeySequence("Ctrl+/"), self, activated=self._shortcut_focus_input)
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.tabs.setCurrentIndex(0))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.tabs.setCurrentIndex(1))
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self.tabs.setCurrentIndex(2))
        QShortcut(QKeySequence("F11"),    self, activated=self._toggle_focus_mode)
        QShortcut(QKeySequence("Ctrl+`"), self, activated=self._shortcut_toggle_terminal)

    def _shortcut_new_chat(self):
        self.tabs.setCurrentIndex(0)
        self.chat_tab._new_conversation()

    def _shortcut_clear_input(self):
        if self.tabs.currentIndex() == 0:
            self.chat_tab.msg_input.clear()

    def _shortcut_focus_input(self):
        if self.tabs.currentIndex() == 0:
            self.chat_tab.msg_input.setFocus()

    def _shortcut_toggle_terminal(self):
        self.term_toggle_btn.setChecked(not self.term_toggle_btn.isChecked())
        self._toggle_terminal()

    def _on_tab_changed(self, index: int):
        """Lazy-load tabs only when clicked."""
        if index == 1:  # Agent tab
            if self.agent_tab is None:
                self.agent_tab = AgentTab()
                self.agent_tab.status_update.connect(self._on_status)
                self.tabs.setTabText(1, "Agent")
                self.tabs.setTabToolTip(1, "")
                self.tabs.widget(1).deleteLater()
                self.tabs.removeTab(1)
                self.tabs.insertTab(1, self.agent_tab, "Agent")
        
        elif index == 2:  # Settings tab
            if self.settings_tab is None:
                self.settings_tab = SettingsTab()
                self.settings_tab.settings_changed.connect(self._on_settings_changed)
                self.tabs.setTabText(2, "Settings")
                self.tabs.setTabToolTip(2, "")
                self.tabs.widget(2).deleteLater()
                self.tabs.removeTab(2)
                self.tabs.insertTab(2, self.settings_tab, "Settings")

    def _toggle_focus_mode(self):
        """F11: hide sidebars + tabs for a distraction-free chat view."""
        self._focus_mode = not self._focus_mode
        if self._focus_mode:
            self.tabs.setCurrentIndex(0)  # always focus on chat
            self._saved_chat_sizes = self.chat_tab._main_splitter.sizes()
            self.chat_tab._main_splitter.setSizes([0, 9999])
            self.tabs.tabBar().setVisible(False)
            self._on_status("Focus mode on  --  press F11 to exit")
        else:
            if self._saved_chat_sizes:
                self.chat_tab._main_splitter.setSizes(self._saved_chat_sizes)
            self.tabs.tabBar().setVisible(True)
            self._on_status("Focus mode off")

    def _sync_terminal_ask_target(self, provider: str, model: str):
        self.terminal.set_ask_target(provider, model)

    def _toggle_terminal(self):
        visible = self.term_toggle_btn.isChecked()
        self.terminal.setVisible(visible)
        if visible:
            self.splitter.setSizes([620, 220])

    def _on_status(self, msg: str):
        self.status_bar.showMessage(msg)
        self.header_status.setText(msg[:60])

    def _on_settings_changed(self, s: Dict):
        font_size = s.get("font_size", 13)
        accent = s.get("accent", COLORS['accent'])
        QApplication.instance().setStyleSheet(STYLESHEET(font_size, accent))
        self.status_bar.showMessage("Settings saved.")

    def _refresh_metrics(self):
        try:
            summary = timer_summary()
            if summary and summary != "No metrics yet.":
                lines = [l.strip() for l in summary.splitlines() if l.strip()]
                self.header_status.setText(" | ".join(lines[:3]))
        except Exception:
            pass

    def closeEvent(self, event):
        self.chat_tab.save_conversations()
        # Stop any running workers
        for worker in [self.chat_tab.worker, self.agent_tab.worker]:
            if worker and worker.isRunning():
                worker.stop()
                worker.wait(2000)
        event.accept()


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def main():
    load_settings()
    start_session()

    app = QApplication(sys.argv)
    app.setApplicationName("SupportLabs sfm")

    font_size = S("font_size", 13)
    accent = S("accent", COLORS['accent'])
    app.setStyleSheet(STYLESHEET(font_size, accent))

    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(COLORS['bg']))
    palette.setColor(QPalette.WindowText,      QColor(COLORS['text']))
    palette.setColor(QPalette.Base,            QColor(COLORS['surface']))
    palette.setColor(QPalette.AlternateBase,   QColor(COLORS['panel']))
    palette.setColor(QPalette.Text,            QColor(COLORS['text']))
    palette.setColor(QPalette.Button,          QColor(COLORS['surface']))
    palette.setColor(QPalette.ButtonText,      QColor(COLORS['text']))
    palette.setColor(QPalette.Highlight,       QColor(accent))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()