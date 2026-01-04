# LocalMind Installation Steps

## ✅ Step 1: Install Ollama (DONE!)

**You already have Ollama installed!** Here's what you have:
- **Ollama Version**: 0.5.7
- **Installed Model**: `deepseek-r1:latest` (4.7 GB)

### If Ollama wasn't installed, here's how to install it:

1. **Download Ollama for Windows**:
   - Go to: https://ollama.ai/download
   - Download the Windows installer
   - Run the installer and follow the prompts

2. **Start Ollama**:
   - Ollama usually starts automatically after installation
   - If not, run: `ollama serve` in a terminal
   - Or start it from the Start Menu

3. **Verify it's running**:
   ```powershell
   ollama list
   ```

### Pull More Models (Optional)

You can install more models if you want:

```powershell
# Popular models to try:
ollama pull llama2          # Meta's Llama 2 (7B)
ollama pull mistral         # Mistral AI model
ollama pull codellama       # Code-focused model
ollama pull phi3            # Microsoft's small, fast model
```

---

## 📦 Step 2: Set Up LocalMind Python Environment

**Do this in your LocalMind project folder:**

```powershell
# Navigate to the project
cd "C:\Users\Edwin\Documents\local ai"

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Step 3: Test LocalMind

Once the environment is set up:

```powershell
# Make sure you're in the project folder with venv activated
cd "C:\Users\Edwin\Documents\local ai"
venv\Scripts\activate

# Check status
python main.py status

# List models
python main.py models

# Start chatting!
python main.py chat
```

---

## 🎯 Quick Test

Try a quick question:

```powershell
python main.py chat "Hello! What can you do?"
```

---

## 📝 Notes

- **Ollama must be running** for LocalMind to work
- If Ollama stops, restart it: `ollama serve`
- Your model `deepseek-r1` is ready to use!
- Check `QUICKSTART.md` for more usage examples


