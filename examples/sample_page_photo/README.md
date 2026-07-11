# Sample page photos

Drop phone photos or screenshots of textbook pages here, then:

```bash
# Offline mock (uses matching .md sidecars if present)
bookworm ingest-pages examples/sample_page_photo --backend mock -d mechanics_demo

# Local multimodal LLM (free via Ollama)
ollama pull moondream
bookworm ingest-pages examples/sample_page_photo --backend ollama -d mechanics_demo \
  --skills free_body,newtons_2nd
```

Supported: `.png` `.jpg` `.jpeg` `.webp` `.gif` `.bmp`
