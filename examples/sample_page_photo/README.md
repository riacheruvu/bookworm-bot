# Sample page photos

Tiny demo assets for `bookworm ingest-pages`.

| File | Role |
|------|------|
| `demo_fbd.png` | Placeholder image (swap for a real page photo) |
| `demo_fbd.md` | Sidecar text for `--backend mock` |

```bash
# Offline mock (uses demo_fbd.md next to the PNG)
bookworm ingest-pages examples/sample_page_photo --backend mock -d mechanics_demo --skills free_body

# Local multimodal LLM (free via Ollama)
ollama pull moondream
bookworm ingest-pages examples/sample_page_photo --backend ollama -d mechanics_demo \
  --skills free_body,newtons_2nd
```

**Full documentation:** [docs/READING.md](../../docs/READING.md)

Supported images: `.png` `.jpg` `.jpeg` `.webp` `.gif` `.bmp`
