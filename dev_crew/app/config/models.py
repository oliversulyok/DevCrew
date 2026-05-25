import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# ARCHITEKTÚRA ÉS PO
architekt_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model_name="openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    max_retries=10,
)

# KÓDOLÁS ÉS TRIAGE
kodolo_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    max_retries=10,
)

# EGYSZERŰ FELADATOK (OpenRouter - Ingyenes modellek)
olcso_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openrouter/openai/gpt-oss-20b:free",
    max_retries=10,
)
