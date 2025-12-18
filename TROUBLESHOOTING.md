# Troubleshooting Guide

Common issues and solutions for LocalMind.

## Installation Issues

### Python Version
**Problem:** `python` command not found or wrong version

**Solution:**
- Ensure Python 3.10+ is installed
- Use `python3` instead of `python` on Linux/Mac
- Check version: `python --version` or `python3 --version`
- Download from: https://www.python.org/downloads/

### Virtual Environment Issues
**Problem:** `venv` module not found

**Solution:**
```bash
# On Windows
python -m pip install --upgrade pip
python -m venv venv

# On Linux/Mac
python3 -m pip install --upgrade pip
python3 -m venv venv
```

### Dependency Installation Fails
**Problem:** `pip install -r requirements.txt` fails

**Solutions:**
1. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Install build tools (Windows):**
   - Install Visual C++ Build Tools
   - Or install Visual Studio with C++ development tools

3. **Use pre-built wheels:**
   ```bash
   pip install --only-binary :all: -r requirements.txt
   ```

4. **Install specific problematic packages separately:**
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   ```

## Ollama Issues

### Ollama Not Running
**Problem:** "Ollama backend not available" or "Connection refused"

**Solutions:**
1. **Start Ollama service:**
   ```bash
   # Windows: Start Ollama from Start Menu
   # Linux/Mac:
   ollama serve
   ```

2. **Check if Ollama is running:**
   ```bash
   ollama list
   ```

3. **Verify Ollama is accessible:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

### No Models Available
**Problem:** "No models available" in model list

**Solution:**
```bash
# Pull a model
ollama pull llama2

# Or try other models
ollama pull mistral
ollama pull codellama
```

### Model Download Fails
**Problem:** Model download times out or fails

**Solutions:**
1. **Check internet connection**
2. **Try again** - downloads can be interrupted
3. **Check disk space** - models can be large (several GB)
4. **Use smaller models** if disk space is limited

## API Backend Issues

### API Key Not Working
**Problem:** "Backend not available" or "Invalid API key"

**Solutions:**
1. **Verify API key is correct:**
   - Check for extra spaces or characters
   - Copy-paste directly from provider's dashboard

2. **Check API key is set:**
   ```bash
   # Check environment variable
   echo $OPENAI_API_KEY  # Linux/Mac
   echo %OPENAI_API_KEY%  # Windows
   ```

3. **Configure via web interface:**
   - Go to http://localhost:5000/configure
   - Enter API key and enable backend

4. **Restart server** after configuring

### Rate Limiting
**Problem:** "Rate limit exceeded" error

**Solutions:**
1. **Wait before retrying** - check `Retry-After` header
2. **Use a different model** or backend
3. **Upgrade API plan** if hitting limits frequently
4. **Use local models** (Ollama) to avoid rate limits

### API Service Down
**Problem:** "Connection error" or "Service unavailable"

**Solutions:**
1. **Check provider status page:**
   - OpenAI: https://status.openai.com
   - Anthropic: https://status.anthropic.com
   - Google: https://status.cloud.google.com

2. **Check internet connection**
3. **Try again later**
4. **Use local models** as fallback

## Web Interface Issues

### Server Won't Start
**Problem:** "Address already in use" or port 5000 in use

**Solutions:**
1. **Use a different port:**
   ```bash
   python main.py web --port 5001
   ```

2. **Kill process using port 5000:**
   ```bash
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   
   # Linux/Mac
   lsof -ti:5000 | xargs kill
   ```

3. **Check if another instance is running**

### Page Won't Load
**Problem:** Browser shows "Connection refused" or blank page

**Solutions:**
1. **Check server is running:**
   ```bash
   python main.py web
   ```

2. **Check URL:** Use `http://localhost:5000` (not `https://`)

3. **Check firewall** isn't blocking port 5000

4. **Try different browser** or clear cache

### Models Not Showing
**Problem:** Model list is empty

**Solutions:**
1. **Refresh the page** (Ctrl+F5 or Cmd+Shift+R)

2. **Check backend is available:**
   - Go to http://localhost:5000/configure
   - Verify backend is enabled

3. **Restart server:**
   ```bash
   # Stop server (Ctrl+C)
   python main.py web
   ```

4. **Check logs** for errors

### Chat Not Working
**Problem:** Messages not sending or no response

**Solutions:**
1. **Check model is selected** in dropdown

2. **Check browser console** (F12) for errors

3. **Verify backend is available:**
   - Check status indicator in header
   - Go to /api/status endpoint

4. **Try different model**

5. **Check network tab** for failed requests

## Configuration Issues

### Config File Errors
**Problem:** "Error loading config" or config file corrupted

**Solutions:**
1. **Backup is created automatically** - check for `.yaml.backup` file

2. **Reset to defaults:**
   ```bash
   # Delete config file (will be recreated)
   rm ~/.localmind/config.yaml  # Linux/Mac
   del %USERPROFILE%\.localmind\config.yaml  # Windows
   ```

3. **Check file permissions** - ensure readable/writable

### Path Issues (Windows)
**Problem:** Path-related errors on Windows

**Solutions:**
1. **Use forward slashes** or raw strings in config
2. **Avoid spaces** in paths if possible
3. **Use absolute paths** instead of relative

## Performance Issues

### Slow Responses
**Problem:** AI responses are very slow

**Solutions:**
1. **Use smaller models** (e.g., 7B instead of 70B)
2. **Use API backends** (faster than local models)
3. **Check system resources:**
   - CPU/GPU usage
   - Available RAM
   - Disk I/O

4. **Close other applications** to free resources

### High Memory Usage
**Problem:** System running out of memory

**Solutions:**
1. **Use smaller models**
2. **Unload models** when not in use (if supported)
3. **Use API backends** instead of local models
4. **Increase system RAM** if possible

### GPU Not Used
**Problem:** Models running on CPU instead of GPU

**Solutions:**
1. **Check GPU drivers** are installed
2. **Install CUDA** (for NVIDIA GPUs)
3. **Check PyTorch** is GPU-enabled:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

4. **Configure GPU in backend settings**

## Module Issues

### Module Not Loading
**Problem:** Module shows as unavailable

**Solutions:**
1. **Check module file exists** in `src/modules/`
2. **Check for import errors** in logs
3. **Verify module implements BaseModule** correctly
4. **Check module is enabled** in configuration

## Conversation Issues

### Conversations Not Saving
**Problem:** Conversations disappear after refresh

**Solutions:**
1. **Check `conversations/` directory exists** and is writable
2. **Check disk space**
3. **Check file permissions**
4. **Review logs** for save errors

### Can't Export Conversation
**Problem:** Export button doesn't work

**Solutions:**
1. **Check browser allows downloads**
2. **Try different format** (JSON vs Markdown)
3. **Check browser console** for errors

## Network Issues

### Can't Access from Other Devices
**Problem:** Can't access web interface from phone/other computer

**Solutions:**
1. **Use 0.0.0.0 instead of localhost:**
   ```bash
   python main.py web --host 0.0.0.0
   ```

2. **Find your IP address:**
   ```bash
   # Windows
   ipconfig
   
   # Linux/Mac
   ifconfig
   ```

3. **Access via IP:** `http://<your-ip>:5000`

4. **Check firewall** allows connections on port 5000

5. **Use QR code** feature in web interface

## Getting Help

### Check Logs
```bash
# Logs are printed to console
# For file logging, configure in logger settings
```

### Common Error Messages

- **"Backend not available"**: Check API key or Ollama is running
- **"Model not found"**: Pull/download the model first
- **"Connection refused"**: Service not running or wrong port
- **"Rate limit exceeded"**: Wait or use different backend
- **"Invalid API key"**: Check key is correct and enabled

### Report Issues
1. **Check existing issues** on GitHub
2. **Include error messages** and logs
3. **Describe steps to reproduce**
4. **Include system information** (OS, Python version, etc.)

## Still Having Issues?

1. **Check the documentation:**
   - `README.md` - Overview
   - `INSTALL_STEPS.md` - Installation guide
   - `API_DOCUMENTATION.md` - API reference

2. **Search GitHub issues** for similar problems

3. **Create a new issue** with:
   - Error messages
   - Steps to reproduce
   - System information
   - Relevant logs

