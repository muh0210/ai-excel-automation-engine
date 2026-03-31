---
description: How to push changes and deploy the AI Excel Automation Engine
---

## Push & Deploy Workflow

Any changes pushed to `main` will auto-deploy to Streamlit Cloud.

// turbo-all

### Steps

1. Stage all changes
```bash
cd "d:\AI Excel Automation Engine" && git add -A
```

2. Commit with a descriptive message
```bash
cd "d:\AI Excel Automation Engine" && git commit -m "your commit message here"
```

3. Push to GitHub (auto-deploys to Streamlit Cloud)
```bash
cd "d:\AI Excel Automation Engine" && git push origin main
```

### Links
- **GitHub**: https://github.com/muh0210/ai-excel-automation-engine
- **Live App**: https://ai-excel-automation-engin-f3sfb7asi9nbulpvdhfexg.streamlit.app/
- **Local Dev**: `python -m streamlit run app.py` → http://localhost:8501
