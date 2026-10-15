# Linux app (Python + PySide6)

Status: S01 scaffold (empty window).

## Run (S01 DoD)

```bash
pip install -r requirements.txt
python main.py
```

Smoke (headless): `QT_QPA_PLATFORM=offscreen timeout 10 python main.py` stays alive.
