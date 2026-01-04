# Complete Setup Guide for LocalMind

## 📋 Everything You Need to Get Started

### Prerequisites

1. **Python 3.8+** (recommended: Python 3.10 or 3.11)
   - Check your version: `python --version`
   - Download from: https://www.python.org/downloads/

2. **pip** (usually comes with Python)
   - Check: `pip --version`

3. **Virtual Environment** (recommended)
   - Python's built-in `venv` module

4. **Git** (optional, if cloning from repository)
   - Download from: https://git-scm.com/downloads

---

## 🚀 Step-by-Step Installation

### Step 1: Navigate to Project Directory

```bash
cd "C:\Users\Edwin\Documents\local ai"
```

### Step 2: Create Virtual Environment (if not already created)

```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Note:** If you get an execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 4: Install All Dependencies

```bash
pip install -r requirements.txt
```

**This installs:**
- ✅ Core dependencies (click, rich, pydantic, pyyaml, python-dotenv)
- ✅ Model backends (ollama, transformers, torch, accelerate)
- ✅ Utilities (requests, aiohttp, tqdm, psutil)
- ✅ Web server (flask, flask-cors)
- ✅ Security (cryptography)
- ✅ Optional: llama-cpp-python (for GGUF models)

**Installation time:** 5-15 minutes depending on your internet speed
- `cryptography` may take a few minutes (compiles C extensions)
- `torch` is large (~2GB) but essential for transformers

### Step 5: Verify Installation

```bash
python main.py version
```

You should see version information.

---

## 🎯 Starting the Web Server

### Option 1: Using the Scripts (Easiest)

**Simple Start:**
```bash
scripts\start-web.bat
```

**Advanced Menu:**
```bash
scripts\start-web-advanced.bat
```

**PowerShell:**
```powershell
.\scripts\start-web.ps1
```

### Option 2: Using Command Line Directly

```bash
# Activate virtual environment first
venv\Scripts\activate.bat

# Start web server
python main.py web --host 0.0.0.0 --port 5000
```

### Option 3: With Custom Options

```bash
# Local only (127.0.0.1)
python main.py web --host 127.0.0.1 --port 5000

# Custom port
python main.py web --host 0.0.0.0 --port 8080

# Debug mode
python main.py web --host 0.0.0.0 --port 5000 --debug
```

---

## 🌐 Accessing the Web Interface

Once the server starts, you'll see:
```
Starting LocalMind Web Server
Starting server on http://0.0.0.0:5000
```

**Access from:**
- **Local machine:** http://localhost:5000
- **Other devices on network:** http://YOUR_IP:5000
  - Find your IP: `ipconfig` (Windows) or check network settings

---

## ⚙️ Configuration (Optional)

### API Keys for Cloud Models

If you want to use cloud-based models (OpenAI, Anthropic, Google, etc.):

**Option 1: Environment Variables**
```bash
set OPENAI_API_KEY=your_key_here
set ANTHROPIC_API_KEY=your_key_here
set GOOGLE_API_KEY=your_key_here
```

**Option 2: Configuration Command**
```bash
python main.py configure
```

**Option 3: Web Interface**
- Visit: http://localhost:5000/configure
- Enter API keys through the web interface

**Note:** You can use LocalMind with just local models (Ollama) - no API keys required!

### Setting Up Ollama (Local Models)

1. **Install Ollama:**
   - Download from: https://ollama.ai
   - Install and start Ollama service

2. **Download Models:**
   ```bash
   ollama pull llama2
   ollama pull mistral
   # etc.
   ```

3. **Verify:**
   ```bash
   python main.py models
   ```

---

## 📦 Complete Dependency List

### Required Dependencies (from requirements.txt)

**Core:**
- `click>=8.1.7` - CLI framework
- `rich>=13.7.0` - Beautiful terminal output
- `pydantic>=2.5.0` - Data validation
- `pyyaml>=6.0.1` - YAML parsing
- `python-dotenv>=1.0.0` - Environment variables

**Model Backends:**
- `ollama>=0.1.0` - Ollama integration
- `transformers>=4.35.0` - HuggingFace models
- `torch>=2.1.0` - PyTorch (large download!)
- `accelerate>=0.25.0` - Model acceleration

**Utilities:**
- `requests>=2.31.0` - HTTP requests
- `aiohttp>=3.9.0` - Async HTTP
- `tqdm>=4.66.0` - Progress bars
- `psutil>=5.9.0` - System monitoring

**Web Server:**
- `flask>=3.0.0` - Web framework
- `flask-cors>=4.0.0` - CORS support

**Security:**
- `cryptography>=41.0.0` - Encryption (may take time to install)

**Optional:**
- `llama-cpp-python>=0.3.0` - GGUF model support

---

## 🔧 Troubleshooting

### Issue: "No module named 'cryptography'"
**Solution:**
```bash
pip install cryptography
# or
pip install -r requirements.txt
```

### Issue: "No module named 'flask'"
**Solution:**
```bash
pip install flask flask-cors
# or
pip install -r requirements.txt
```

### Issue: Script can't find main.py
**Solution:** Scripts now automatically change to project root. If still having issues:
- Make sure you're running from the project directory
- Or use: `python main.py web` directly

### Issue: Virtual environment not activating
**Solution:**
- Make sure you're in the project directory
- Check that `venv\Scripts\activate.bat` exists
- Try: `python -m venv venv` to recreate

### Issue: Port 5000 already in use
**Solution:**
```bash
# Use a different port
python main.py web --port 5001
```

### Issue: Backend not available warnings
**Note:** These are just warnings if API keys aren't configured. The server will still work with local models (Ollama).

---

## ✅ Verification Checklist

Before starting, verify:

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Virtual environment created (`venv` folder exists)
- [ ] Virtual environment activated (see `(venv)` in prompt)
- [ ] All dependencies installed (`pip list` shows packages)
- [ ] `main.py` exists in project root
- [ ] `requirements.txt` exists
- [ ] Port 5000 is available (or use different port)

**Quick test:**
```bash
python main.py version
python main.py status
```

---

## 🎉 You're Ready!

Once everything is installed:

1. **Start the server:**
   ```bash
   scripts\start-web.bat
   ```

2. **Open your browser:**
   ```
   http://localhost:5000
   ```

3. **Start chatting with AI models!**

---

## 📚 Additional Resources

- **Quick Start Guide:** `docs/QUICKSTART.md`
- **API Documentation:** `docs/API_DOCUMENTATION.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **Model Management:** `docs/MODEL_MANAGEMENT.md`
- **Web Interface Guide:** `docs/WEB_INTERFACE.md`

---

## 🆘 Need Help?

- Check the troubleshooting guide: `docs/TROUBLESHOOTING.md`
- Review error messages carefully
- Make sure all dependencies are installed
- Verify Python version compatibility

---

**Last Updated:** After refactoring and cleanup
**Status:** ✅ All scripts fixed and ready to use

