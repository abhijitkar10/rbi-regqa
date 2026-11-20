"""One chat() call over every free OpenAI-compatible endpoint we use.

Keys come from ~/.config/llm-keys/llm.env (or the environment); nothing here prints them.
Usage: chat("groq:llama-3.1-8b-instant", system, user)
"""
import os, time
from pathlib import Path
from openai import OpenAI

BASES = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "cerebras": ("https://api.cerebras.ai/v1", "CEREBRAS_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1", "MISTRAL_API_KEY"),
    "sambanova": ("https://api.sambanova.ai/v1", "SAMBANOVA_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
}
_clients = {}


def _key(name):
    if name not in os.environ:
        env = Path.home() / ".config/llm-keys/llm.env"
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip().removeprefix("export "), v.strip().strip('"').strip("'"))
    return os.environ[name]


def client(provider):
    if provider not in _clients:
        base, keyname = BASES[provider]
        _clients[provider] = OpenAI(base_url=base, api_key=_key(keyname), max_retries=0, timeout=120)
    return _clients[provider]


def chat(model, system, user, max_tokens=2048, temperature=0.0, tries=6, **kw):
    provider, name = model.split(":", 1)
    for i in range(tries):
        try:
            r = client(provider).chat.completions.create(
                model=name, max_tokens=max_tokens, temperature=temperature,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
            return r.choices[0].message.content or ""
        except Exception as e:  # 429 / 5xx on free tiers: back off and retry
            if i == tries - 1:
                raise
            time.sleep(min(60, 5 * 2 ** i))


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:] or BASES:
        try:
            ids = sorted(m.id for m in client(p).models.list().data)
            print(f"{p}: {len(ids)} models: {', '.join(ids[:60])}")
        except Exception as e:
            print(f"{p}: ERROR {type(e).__name__} {str(e)[:120]}")
