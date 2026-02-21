# WhatsApp Agent

An AI-powered conversational agent built with **LangGraph**, featuring long-term memory, speech synthesis, speech recognition, and image generation — designed to plug into WhatsApp.

---

## Features

| Capability | Technology |
|---|---|
| Conversational AI | Groq — `llama-3.1-8b-instant` |
| Speech-to-Text | Groq — `whisper-large-v3-turbo` |
| Text-to-Speech | edge-tts (Microsoft Edge, free) |
| Image Generation | RapidAPI Flux |
| Vision / Image-to-Text | Groq — `llama-4-scout-17b-16e-instruct` |
| Long-term Memory | Qdrant Cloud + `all-MiniLM-L6-v2` embeddings |
| Orchestration | LangGraph `StateGraph` |

---

## Architecture

```
User Message
     │
     ▼
memory_extraction_node   ← stores key facts to Qdrant
     │
     ▼
router_node              ← classifies: conversation / image / audio
     │
     ▼
memory_injection_node    ← retrieves relevant memories from Qdrant
     │
     ├─ conversation_node
     ├─ image_node        ← generates image via RapidAPI Flux
     └─ audio_node        ← synthesizes speech via edge-tts
     │
     ▼
summarize_node (optional) ← trims history when message count is high
     │
     ▼
Response
```

---

## Project Structure

```
Whatsapp-Agent/
├── core/
│   ├── settings.py              # Pydantic-settings config (.env)
│   ├── prompts.py               # All LLM prompts
│   ├── graph/
│   │   ├── graph.py             # LangGraph StateGraph definition
│   │   ├── nodes.py             # All graph nodes
│   │   ├── edges.py             # Conditional edge logic
│   │   ├── state.py             # AICompanionState TypedDict
│   │   └── utils/
│   │       ├── chains.py        # LangChain chain factories
│   │       └── helpers.py       # Module getters, parsers
│   └── modules/
│       ├── image/
│       │   ├── text_to_image.py # RapidAPI Flux image generation
│       │   └── image_to_text.py # Groq vision
│       ├── memory/
│       │   ├── memory_manager.py
│       │   └── vector_store.py  # Qdrant singleton
│       └── speech/
│           ├── speech_to_text.py
│           └── text_to_speech.py
├── demo.py                      # CLI demo (interactive loop)
├── requirements.txt
└── .env                         # API keys (not committed)
```

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/your-username/Whatsapp-Agent.git
cd Whatsapp-Agent
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your keys:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id
RAPIDAPI_KEY=your_rapidapi_key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

> **Qdrant**: Create a free cluster at [cloud.qdrant.io](https://cloud.qdrant.io).  
> **RapidAPI Flux**: Subscribe at [rapidapi.com/ai-text-to-image-generator-flux-free-api](https://rapidapi.com).  
> **Groq**: Get a free API key at [console.groq.com](https://console.groq.com).

### 3. Run the demo

```bash
python demo.py
```

---

## Usage

```
=== WhatsApp Agent Demo ===

You: hey, my name is Alex
[Agent]: Hey Alex! Great to meet you...

You: can you generate an image of a dog on Mars
[Agent]: Here's your image!
[Image saved]: generated_images/image_<uuid>.webp

You: say that out loud
[Agent]: Sure!
[Audio saved]: demo_audio.mp3
```

**Routing keywords** (handled automatically by the LLM router):

| Intent | Example |
|---|---|
| Conversation | any normal message |
| Image | "generate an image of...", "show me a picture of..." |
| Audio | "say that out loud", "read that to me" |

---

## Requirements

- Python 3.9+
- Groq API key (free tier available)
- Qdrant Cloud account (free tier available)
- RapidAPI key for Flux image generation

