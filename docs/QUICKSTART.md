# LocalMind Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Ollama (Recommended)

Ollama is the easiest way to run local models:

1. **Download Ollama**: https://ollama.ai
2. **Install and run Ollama**
3. **Pull a model**:
   ```bash
   ollama pull llama2
   # or try other models:
   # ollama pull mistral
   # ollama pull codellama
   ```

### Step 2: Set Up LocalMind

```bash
# Navigate to project
cd "C:\Users\Edwin\Documents\local ai"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run LocalMind

```bash
# Check status
python main.py status

# List available models
python main.py models

# Start interactive chat
python main.py chat

# Or ask a quick question
python main.py chat "What is Python?"

# Run setup wizard
python main.py setup
```

## 📖 Example Usage

### Interactive Chat Mode

```bash
python main.py chat
```

Then type your questions:
```
You: Explain quantum computing
LocalMind: [Response...]

You: Write a Python function to sort a list
LocalMind: [Response...]

You: exit
```

### Single Query Mode

```bash
python main.py chat "Write a hello world in Python"
```

### With Options

```bash
# Use specific model
python main.py chat "Hello" --model llama2

# Adjust creativity (temperature)
python main.py chat "Write a story" --temperature 0.9

# Use system prompt
python main.py chat "Explain AI" --system "You are a teacher"
```

## 🎯 Next Steps

1. **Try different models**: Pull more models with Ollama
2. **Customize config**: Edit `~/.localmind/config.yaml`
3. **Build modules**: Create custom modules in `src/modules/`
4. **Read docs**: Check `DEVELOPMENT_PLAN.md` for architecture

## 🐛 Troubleshooting

### "No models available"
- Make sure Ollama is running: `ollama list`
- Pull a model: `ollama pull llama2`
- Check status: `python main.py status`

### "Backend not available"
- Verify Ollama is installed and running
- Check if Ollama is on port 11434: `http://localhost:11434/api/tags`
- Try: `python main.py setup`

### Import errors
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## 💡 Tips

- **First time?** Run `python main.py setup` for guided setup
- **Want faster responses?** Use smaller models like `llama2:7b`
- **Need coding help?** Pull `codellama` model: `ollama pull codellama`
- **Check what's available**: `python main.py models`

Happy chatting! 🤖

