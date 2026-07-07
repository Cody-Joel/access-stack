# OpiGuard — Op Renamed

**OpiGuard** is the new name for the Op local AI studio desktop app.

## Why the rename

"Op" was ambiguous (operations? network stack? short for opus?). OpiGuard is:
- **Opi** — short for *opinion* / *operational intelligence* / AI Ops
- **Guard** — the monitoring and safety angle (SentinelBench, value alignment, agent supervision)

The name fits the project's actual purpose: an AI assistant that watches its own behavior and helps you audit other AI systems.

---

## What OpiGuard is

A WinUI 3 / .NET 10 unpackaged desktop app for local AI chat, agent workflows, and safety monitoring.

**Key capabilities:**
- Multi-session chat with streaming (Ollama, Anthropic, NVIDIA NIM, PrivateGPT)
- ReAct agent loop with real tools (read_file, list_dir, search_docs, run_command)
- Slide-up PowerShell terminal with `ask` command (type `ask claude "question"` in-shell)
- Prompt library with personas and user-saved prompts
- Export: Markdown, TXT, JSON, HTML

---

## Architecture

```
OpiGuard/
├── Services/
│   ├── OllamaService.cs        ← local model discovery + streaming
│   ├── ClaudeService.cs        ← Anthropic SSE, x-api-key auth, cost tracking
│   ├── NimService.cs           ← NVIDIA NIM (OpenAI-compat SSE)
│   └── PrivateGptService.cs    ← local RAG via PrivateGPT
├── Pages/
│   ├── ChatPage.xaml           ← multi-session chat, provider dropdown
│   ├── AgentPage.xaml          ← ReAct loop, tool results inline
│   └── SettingsPage.xaml       ← API keys, model defaults
├── Models/
│   └── AppSettings.cs          ← AnthropicApiKey, AnthropicBaseUrl, etc.
└── MainWindow.xaml             ← activity bar, terminal, slide-up pane
```

---

## Design patterns

### Streaming over SSE
All providers stream tokens via Server-Sent Events. The pattern is identical across providers:
```csharp
// Each provider service exposes:
IAsyncEnumerable<string> StreamAsync(string model, string system, string user)
```
The ChatPage subscribes to this and appends each token to the message bubble.

### Cost tracking
`ClaudeService` maintains session-level token counts and calculates cost at `$3/M input, $15/M output` (claude-sonnet-5 pricing). Cost is shown in the sidebar.

### Terminal `ask` command
The embedded PowerShell terminal intercepts lines starting with `ask` and routes them through the active provider:
```
ask claude "what is the capital of France?"
ask ollama llama3 "explain async/await in C#"
```

### Provider dropdown wiring
Every provider change updates a `CurrentProvider` binding that all streaming calls reference. No service is instantiated until first use.

---

## Roadmap

| Priority | Feature | Status |
|---|---|---|
| High | Mix vocals + beat WAV export | In progress (MixingSampleProvider) |
| High | Settings page — soundfont picker, model defaults | Stub only |
| Medium | AI beat generator (Ollama JSON → sequencer grid) | Designed, not built |
| Medium | MCP tool provider (McpToolProvider : IAgentTool) | Planned |
| Low | Groq provider (via NimService SSE pattern) | Planned |

---

## Color palette

Matches Access-Stack and Riff — same hex values across all three projects.

```
bg:      #0d0f14   main background
panel:   #131620   sidebar, chrome
surface: #1b1f2e   input fields, cards
border:  #252a3d   all borders
accent:  #4f8ef7   primary action
green:   #22d3a5   success
yellow:  #f59e0b   warning
red:     #ef4444   error
text:    #e2e8f0   primary text
muted:   #64748b   secondary text
```

---

## Relationship to other projects

| Project | Type | Purpose |
|---|---|---|
| Access-Stack | PyQt5 Python | LLM evaluation toolkit (SpecLab, SentinelBench, SkillStack) |
| **OpiGuard** | WinUI 3 / .NET | Local AI studio — chat, agents, safety monitoring |
| Riff | WPF / .NET | Music production — instruments, sequencer, AI beat generation |

All three share the same design language and sit on the same local Ollama backend.
