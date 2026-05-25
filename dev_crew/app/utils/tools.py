from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from utils.vector_store import get_chroma_db

class VectorSearchInput(BaseModel):
    query: str = Field(description="A szemantikus keresési kifejezés a projekthez.")

class ProjectSearchTool(BaseTool):
    name: str = "Search Project Workspace"
    description: str = (
        "Ezzel a szemantikus kereső eszközzel kereshetsz a projekt forráskódjában, "
        "specifikációiban, tesztjeiben és dokumentációjában. Kereshetsz osztálynevekre, "
        "követelményekre, vagy funkciókra."
    )
    args_schema: Type[BaseModel] = VectorSearchInput
    project_dir: str = ""

    def __init__(self, project_dir: str, **kwargs):
        super().__init__(project_dir=project_dir, **kwargs)

    def _run(self, query: str) -> str:
        try:
            db = get_chroma_db(self.project_dir)
            docs = db.similarity_search(query, k=5)
            if not docs:
                return "Nem találtam egyező dokumentumrészt a keresett kifejezésre."
            
            results = []
            for doc in docs:
                source = doc.metadata.get("source", "ismeretlen")
                content = doc.page_content
                results.append(f"--- Fájl: {source} ---\n{content}\n")
            return "\n".join(results)
        except Exception as e:
            return f"Hiba történt a keresés során: {str(e)}"
