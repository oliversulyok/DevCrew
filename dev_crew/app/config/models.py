import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# ARCHITEKTÚRA ÉS PO
architekt_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model_name="openrouter/qwen/qwen3.6-plus-preview:free",
    max_retries=10,
)

# KÓDOLÁS ÉS TRIAGE
kodolo_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openrouter/stepfun/step-3.5-flash:free",
    max_retries=10,
)

# EGYSZERŰ FELADATOK (OpenRouter - Ingyenes modellek)
olcso_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openrouter/nvidia/nemotron-3-nano-30b-a3b:free",
    max_retries=10,
)
