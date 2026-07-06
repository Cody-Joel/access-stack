 UI — ready to use

This folder contains the `cfui` application, including a Gradio web app and a desktop UI.

Setup:
  1. cd PATHTOYOURFOLDER 
  2. python -m venv .venv
  3. .\.venv\Scripts\Activate.ps1
  4. pip install -r requirements.txt
  5. copy .env.example .env
  6. edit .env with any API keys you want to use

Run:
  python app.py
  python desktop_app.py
  python qt_app.py

What is included:
  - qtUI with chat, research guide, tools, SpecLab, and SentinelBench
  - Desktop UI alternative
  - Safe runtime tools and session metrics
  - Model registry in models.json