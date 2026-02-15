# Ollama Model Options — Reference

## Overview

Orangutan Code passes generation parameters to Ollama via the `options` dict
in `ollama_client.py:MODEL_OPTIONS`. These parameters control how the model
generates text — affecting quality, speed, determinism, and resource usage.

The `keep_alive` parameter is passed separately at the top level of the
`client.chat()` call.

## Current Configuration

Defined in `orangutan/ollama_client.py`:

```python
MODEL_OPTIONS = {
    "temperature": 0.4,
    "top_p": 0.9,
    "top_k": 40,
    "num_ctx": 8192,
    "num_predict": -1,
    "repeat_penalty": 1.1,
    "stop": ["[END]"],
}
```

### Parameter Details

| Parameter | Value | Why |
|-----------|-------|-----|
| `temperature` | `0.4` | Lower than default (0.8). Produces more focused, deterministic output suitable for code generation. |
| `top_p` | `0.9` | Nucleus sampling: keeps the top 90% of probability mass. Balances diversity and coherence. |
| `top_k` | `40` | Limits token candidates per step to 40. Prevents low-probability noise. |
| `num_ctx` | `8192` | Context window size in tokens. 4x larger than the default (2048). Allows the model to process longer conversations and larger code files. |
| `num_predict` | `-1` | No limit on response length. The model generates until it naturally stops or hits a stop sequence. |
| `repeat_penalty` | `1.1` | Penalizes tokens that already appeared. Prevents repetitive output patterns. |
| `stop` | `["[END]"]` | Custom stop sequence. The model stops generating when it emits `[END]`. |
| `keep_alive` | `"10m"` | Keeps the model loaded in GPU/RAM for 10 minutes after the last request. Avoids cold-start latency between interactions. Passed at the `client.chat()` level, not inside `options`. |

## All Available Ollama Parameters

These parameters can be added to `MODEL_OPTIONS` if needed:

### Sampling Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `temperature` | 0.8 | Controls randomness. 0.0 = deterministic, 2.0 = very random. |
| `top_p` | 0.9 | Nucleus sampling threshold. |
| `top_k` | 40 | Number of top tokens to consider. |
| `typical_p` | 1.0 | Typical sampling parameter. Lower values increase coherence. |
| `tfs_z` | 1.0 | Tail-free sampling. Lower values reduce low-quality tokens. |
| `mirostat` | 0 | Mirostat algorithm (0=off, 1=v1, 2=v2). Controls perplexity. |
| `mirostat_tau` | 5.0 | Target perplexity for Mirostat. |
| `mirostat_eta` | 0.1 | Learning rate for Mirostat. |

### Generation Control

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_predict` | 128 | Max tokens to generate. -1 = unlimited, -2 = fill context. |
| `num_ctx` | 2048 | Context window size (tokens). Larger = more memory. |
| `stop` | [] | Stop sequences. Generation stops when any is emitted. |
| `seed` | 0 | Random seed for reproducibility. Same seed = same output. |

### Repetition Control

| Parameter | Default | Description |
|-----------|---------|-------------|
| `repeat_penalty` | 1.1 | Penalty for repeated tokens. Higher = less repetition. |
| `repeat_last_n` | 64 | How far back to look for repetition (tokens). |
| `presence_penalty` | 0.0 | Penalizes tokens that appeared at all. |
| `frequency_penalty` | 0.0 | Penalizes tokens based on how often they appeared. |
| `penalize_newline` | true | Whether to penalize newline tokens. |

### Hardware / Performance

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_gpu` | auto | Number of GPU layers. 0 = CPU only. |
| `num_thread` | auto | CPU threads for inference. |
| `num_batch` | 512 | Batch size for prompt processing. |
| `low_vram` | false | Reduce VRAM usage at the cost of speed. |
| `f16_kv` | true | Use float16 for key/value cache. |
| `use_mmap` | true | Memory-map model files. |
| `use_mlock` | false | Lock model in memory (prevents swap). |
| `numa` | false | NUMA-aware allocation. |

### Top-Level Parameters (outside `options`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `keep_alive` | `"5m"` | How long to keep model loaded after last request. `"0"` = unload immediately. |
| `format` | none | Force output format. `"json"` for structured JSON output. |
| `tools` | none | Native function calling definitions (OpenAI-compatible format). |

## Tuning Guidelines

### For more deterministic/technical output
```python
{"temperature": 0.2, "top_p": 0.8, "top_k": 20, "repeat_penalty": 1.2}
```

### For more creative/exploratory output
```python
{"temperature": 0.8, "top_p": 0.95, "top_k": 60, "repeat_penalty": 1.0}
```

### For large projects (more context)
```python
{"num_ctx": 16384}  # requires more VRAM/RAM
```

### For low-resource machines
```python
{"num_ctx": 4096, "num_gpu": 0, "num_thread": 4, "low_vram": True}
```

## How Parameters Are Passed

In `orangutan/ollama_client.py`, the `OllamaChat.send()` method passes them to Ollama:

```python
stream = self.client.chat(
    model=MODEL,
    messages=self.messages,
    stream=True,
    options=self.options,      # MODEL_OPTIONS dict
    keep_alive="10m",          # top-level parameter
)
```

The `OllamaChat.__init__()` accepts an optional `options` override:

```python
chat = OllamaChat(system_prompt)                    # uses MODEL_OPTIONS
chat = OllamaChat(system_prompt, options={...})     # custom options
```
