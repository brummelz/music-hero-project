# Music Hero Project

A Python application with potential for compilation into an executable (.exe).

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
   - On Windows (cmd): `venv\Scripts\activate.bat`
   - On macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running

```bash
python main.py
```

## Building

To compile to an executable (when ready), use PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile main.py
```
