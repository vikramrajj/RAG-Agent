# 🤖 Lightweight Reasoning Models Integration Guide

## Overview

This guide explains how to use lightweight reasoning models (Mistral, Llama, Phi-3, etc.) with your SAT (Student Assistance Tool) interface for fast, local AI chat.

---

## 🎯 Available Models

### ⚡ Ultra-Fast Models (< 1GB)
**Best for**: Quick responses, low-end devices

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Phi-3 Mini** | 0.5GB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Quick Q&A, Simple homework |
| **TinyLlama** | 0.6GB | ⚡⚡⚡⚡⚡ | ⭐⭐ | Very fast chat, Basic questions |

### ⚖️ Balanced Models (1-4GB)  
**Best for**: General use, good performance

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Mistral 7B** ⭐ | 4.1GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Homework, Essays, Research |
| **Llama 3.2 (3B)** | 2.0GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Academic Q&A, Code help |
| **Gemma 2 (2B)** | 1.6GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Summaries, Study guides |

### 🌟 Quality Models (4-8GB)
**Best for**: Complex tasks, best results

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **Llama 3.1 (8B)** | 4.7GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Long documents, Reasoning |
| **Qwen 2.5 (7B)** | 4.7GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Math, Logic, Code |
| **DeepSeek R1** | 1.0GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Math reasoning, Problem solving |

---

## 🚀 Quick Start

### Step 1: Install Ollama

**Windows:**
```powershell
# Download from https://ollama.ai/download
# Or use winget:
winget install Ollama.Ollama
```

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Start Ollama Server

```bash
ollama serve
```

Leave this running in the background.

### Step 3: Pull Your First Model

```bash
# Recommended: Mistral (best balance)
ollama pull mistral:7b

# Or start with something faster:
ollama pull phi3:3.8b

# Or for best quality:
ollama pull llama3.1:8b
```

### Step 4: Start SAT Interface

```powershell
cd "c:\Users\vikra\Downloads\RAG Agent"
python agent_bridge.py
```

### Step 5: Access SAT

Open your browser: `http://localhost:8000/sat`

---

## 💡 Model Selection Guide

### For Different Tasks:

**Quick Homework Help:**
```
Recommended: Phi-3 Mini, Gemma 2
Why: Fast responses, good for simple questions
```

**Essay Writing:**
```
Recommended: Mistral, Llama 3.1
Why: Better language quality, coherent long-form text
```

**Math & Logic:**
```
Recommended: Qwen 2.5, DeepSeek R1, Llama 3.1
Why: Specialized reasoning capabilities
```

**Research & Analysis:**
```
Recommended: Llama 3.1, Mistral
Why: Better understanding, large context windows
```

**Coding Help:**
```
Recommended: Llama 3.1, Qwen 2.5
Why: Code-aware, good at debugging
```

**Low RAM (< 4GB):**
```
Recommended: Phi-3 Mini, TinyLlama
Why: Smallest models that still work well
```

---

## 🔧 Configuration

### Environment Variables

Add to your `.env` file:

```env
# Model Configuration
DEFAULT_MODEL=mistral              # Your default model
FALLBACK_MODEL=phi3-mini          # Fallback if default fails
OLLAMA_BASE_URL=http://localhost:11434

# Model Settings
MODEL_TEMPERATURE=0.1              # Lower = more focused (0.0-1.0)
MODEL_MAX_TOKENS=2048             # Max response length
MODEL_TOP_P=0.9                   # Nucleus sampling

# Auto-download
AUTO_PULL_MODELS=true             # Auto-download missing models
```

### Python API Usage

```python
from model_manager import get_model_manager, load_model, chat

# Load a model
load_model("mistral")  # Will auto-download if needed

# Chat
response = chat(
    message="Explain photosynthesis",
    system_prompt="You are a helpful tutor"
)

print(response['content'])
print(f"Speed: {response['tokens_per_second']:.1f} tokens/sec")
```

---

## 📊 Performance Comparison

### Response Speed (Tokens/Second)

On typical laptop (16GB RAM, CPU only):

```
TinyLlama:    ~100-120 tokens/sec  ⚡⚡⚡⚡⚡
Phi-3 Mini:   ~80-100 tokens/sec   ⚡⚡⚡⚡⚡
Gemma 2 2B:   ~60-80 tokens/sec    ⚡⚡⚡⚡
Llama 3.2 3B: ~50-70 tokens/sec    ⚡⚡⚡⚡
Mistral 7B:   ~30-50 tokens/sec    ⚡⚡⚡⚡
Llama 3.1 8B: ~25-40 tokens/sec    ⚡⚡⚡
Qwen 2.5 7B:  ~30-45 tokens/sec    ⚡⚡⚡
```

### Quality Comparison

**Simple Question: "What is 2+2?"**
- All models: ✅ Correct

**Essay Writing: "Explain climate change"**
- TinyLlama: ⭐⭐ Basic, short
- Phi-3 Mini: ⭐⭐⭐ Good, structured
- Mistral: ⭐⭐⭐⭐ Excellent, detailed
- Llama 3.1: ⭐⭐⭐⭐⭐ Outstanding, comprehensive

**Math Problem: "Solve quadratic equation"**
- TinyLlama: ⭐⭐ Sometimes correct
- Phi-3 Mini: ⭐⭐⭐ Usually correct
- Qwen 2.5: ⭐⭐⭐⭐⭐ Always correct, shows steps
- DeepSeek R1: ⭐⭐⭐⭐⭐ Correct, explains reasoning

---

## 🎮 Using the SAT Interface

### Model Selector

The SAT UI now includes a model selector:

```
┌─────────────────────────────────┐
│ Model: [Mistral 7B ▼]          │
│ ⚡⚡⚡⚡ Speed                   │
│ ⭐⭐⭐⭐ Quality                 │
│ RAM: 8GB recommended            │
└─────────────────────────────────┘
```

### Switching Models On-The-Fly

1. Click the model dropdown
2. Select your preferred model
3. If not downloaded, click "Download Model"
4. Chat continues with new model

### Model Status Indicators

- 🟢 **Ready** - Model loaded and ready
- 🟡 **Loading** - Model is being loaded
- 🔴 **Not Available** - Model needs to be downloaded
- ⏳ **Downloading** - Model is being pulled

---

## 🔄 API Integration

### REST API Endpoints

**Get Available Models:**
```bash
curl http://localhost:8000/api/models
```

**Load Model:**
```bash
curl -X POST http://localhost:8000/api/models/load \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral"}'
```

**Chat with Model:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum physics",
    "model": "mistral",
    "temperature": 0.1
  }'
```

**Get Model Info:**
```bash
curl http://localhost:8000/api/models/current
```

---

## 🎯 Recommended Setups

### For Students (4-8GB RAM):
```bash
# Download these 3 models:
ollama pull phi3:3.8b          # Fast for quick questions
ollama pull mistral:7b         # Main workhorse
ollama pull qwen2.5:7b        # For math problems

# Set default:
DEFAULT_MODEL=mistral
```

### For Low-End Devices (2-4GB RAM):
```bash
# Download these 2 models:
ollama pull tinyllama:1.1b     # Super fast
ollama pull phi3:3.8b          # Better quality

# Set default:
DEFAULT_MODEL=phi3-mini
```

### For Power Users (16GB+ RAM):
```bash
# Download these 4 models:
ollama pull phi3:3.8b          # Quick questions
ollama pull mistral:7b         # General use
ollama pull llama3.1:8b        # Best quality
ollama pull qwen2.5:7b        # Math/code

# Set default:
DEFAULT_MODEL=llama3.1
```

---

## 📝 Usage Examples

### Example 1: Quick Homework Help

```python
# Use fast model for quick answers
from model_manager import load_model, chat

load_model("phi3-mini")

response = chat(
    message="What's the capital of France?",
    system_prompt="Answer concisely"
)

print(response['content'])
# Output: "Paris"
# Speed: ~100 tokens/sec
```

### Example 2: Essay Writing

```python
# Use quality model for essays
load_model("mistral")

response = chat(
    message="Write a 200-word essay on renewable energy",
    system_prompt="You are an academic writing assistant",
    temperature=0.3  # Higher for creative writing
)

print(response['content'])
# Output: Detailed, well-structured essay
# Speed: ~40 tokens/sec
```

### Example 3: Math Problem

```python
# Use reasoning model for math
load_model("qwen2.5")

response = chat(
    message="Solve: x² + 5x + 6 = 0",
    system_prompt="Show step-by-step solution"
)

print(response['content'])
# Output: Detailed solution with steps
```

---

## 🐛 Troubleshooting

### "Ollama not responding"
```bash
# Check if Ollama is running:
curl http://localhost:11434/api/tags

# If not working, restart Ollama:
# Windows: Restart Ollama app
# Mac/Linux:
ollama serve
```

### "Model not found"
```bash
# Pull the model manually:
ollama pull mistral:7b

# List downloaded models:
ollama list
```

### "Out of memory"
```bash
# Use a smaller model:
ollama pull phi3:3.8b

# Or adjust context length in code:
MAX_TOKENS=1024  # Reduce from 2048
```

### Slow responses
```bash
# Try smaller/faster model:
ollama pull tinyllama:1.1b

# Or reduce max tokens:
MODEL_MAX_TOKENS=1024
```

---

## 📚 Advanced Configuration

### Custom Model Parameters

```python
from model_manager import generate

response = generate(
    prompt="Explain AI",
    temperature=0.7,      # Creativity (0.0-1.0)
    max_tokens=1024,      # Response length
    system_prompt="You are an expert",
)
```

### Conversation History

```python
from model_manager import chat

history = [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."},
]

response = chat(
    message="What are its main features?",
    conversation_history=history
)
```

### Model Recommendations

```python
from model_manager import get_model_manager

manager = get_model_manager()

# Get recommendations for your use case:
recommendations = manager.recommend_for_use_case(
    use_case="homework_help",
    available_ram_gb=8
)

for rec in recommendations:
    print(f"{rec['display_name']}: {rec['description']}")
```

---

## 🎓 Best Practices

### 1. Start Small
Begin with Phi-3 Mini or Mistral, then try larger models if needed.

### 2. Match Model to Task
- Quick questions → Fast models (Phi-3, TinyLlama)
- Essays/Research → Quality models (Mistral, Llama 3.1)
- Math/Code → Reasoning models (Qwen, DeepSeek R1)

### 3. Adjust Temperature
- Factual answers: temperature = 0.1
- Creative writing: temperature = 0.5-0.7
- Brainstorming: temperature = 0.8-1.0

### 4. Monitor RAM Usage
- Keep Task Manager open
- If RAM > 90%, use smaller model
- Close unnecessary applications

### 5. Cache Models
Downloaded models stay on disk (~4-26GB per model).
Only download what you'll use regularly.

---

## 📊 Resource Requirements

### Minimum:
- **RAM:** 2GB
- **Disk:** 1GB
- **Model:** TinyLlama or Phi-3 Mini

### Recommended:
- **RAM:** 8GB
- **Disk:** 10GB
- **Model:** Mistral or Llama 3.2

### Optimal:
- **RAM:** 16GB+
- **Disk:** 50GB
- **Model:** Llama 3.1 + others

---

## 🔗 Useful Links

- **Ollama**: https://ollama.ai
- **Model Library**: https://ollama.ai/library
- **Documentation**: https://github.com/ollama/ollama
- **Community**: https://discord.gg/ollama

---

## 📈 Next Steps

1. ✅ Install Ollama
2. ✅ Pull Mistral model
3. ✅ Start SAT interface
4. ✅ Test with different models
5. ✅ Choose your favorites
6. ✅ Customize for your needs

**Happy Learning! 🎓✨**
