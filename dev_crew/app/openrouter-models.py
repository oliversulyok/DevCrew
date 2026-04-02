import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
def get_free_groq_models():
# Groq API kulcs és URL lekérdezés
    api_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # print(json.dumps(response.json(), indent=4))
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        full_data = response.json()
        # Szűrés az ingyenes modellekre (ahol az ár 0)
        free_models = []
        for model in full_data.get('data', []):
            pricing = model.get('pricing', {})
            # Biztosítjuk, hogy csak a 0 árasak kerüljenek be
            if float(pricing.get('prompt', 1)) == 0 and float(pricing.get('completion', 1)) == 0:
                # Olyan formátumot készítünk, ami hasonlít a Groq exportodra
                simplified_model = {
                    "id": model.get("id"),
                    "object": "model",
                    "created": model.get("created"),
                    "owned_by": model.get("id", "").split('/')[0] if "/" in model.get("id", "") else "unknown",
                    "active": True,
                    "context_window": model.get("context_length"),
                    "public_apps": None,
                    "max_completion_tokens": model.get("top_provider", {}).get("max_completion_tokens"),
                    "knowledge_cutoff": model.get("knowledge_cutoff", "N/A"),
                    "recommended_for": model.get("description", "A gyártó specifikációja alapján")
                }
                free_models.append(simplified_model)

        # Az eredeti struktúra visszaállítása a szűrt adatokkal
        output = {
            "object": "list",
            "data": free_models
        }

        # Kiíratás szép, formázott JSON-ként
        print(json.dumps(output, indent=4))

    except Exception as e:
        print(f"Hiba történt: {e}")

# OpenRouter API kulcs és URL lekérdezés
def get_free_openrouter_models():
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Csak azokat a modelleket tartjuk meg, ahol a prompt és a completion is 0
        free_models = [
            model for model in data.get('data', [])
            if float(model.get('pricing', {}).get('prompt', 1)) == 0 and 
               float(model.get('pricing', {}).get('completion', 1)) == 0
        ]

        print(f"{'ID':<45} | {'Context':<8} | {'Tools?':<6} | {'Cutoff':<10} | {'Megjegyzés / Javaslat (Leírásból)'}")
        print("-" * 120)

        for m in free_models:
            m_id = m.get('id', 'N/A')
            # Rövidítjük az ID-t ha túl hosszú, hogy beférjen
            display_id = (m_id[:42] + '..') if len(m_id) > 42 else m_id
            
            context = m.get('context_length', 'N/A')
            
            # Ellenőrizzük, hogy támogatja-e a 'tools' vagy 'function_calling' paramétert
            params = m.get('supported_parameters', [])
            has_tools = "Igen" if any(p in params for p in ['tools', 'function_call']) else "Nem"
            
            # Cutoff lekérése
            cutoff = m.get('knowledge_cutoff')
            if not cutoff:
                cutoff = "N/A"
            elif 'T' in cutoff:
                cutoff = cutoff.split('T')[0] # Csak a dátum része

            # A javasolt felhasználás általában csak a leírásban vagy az architektúrában szerepel
            desc = m.get('description') or 'N/A'
            desc = desc.replace('\n', ' ')
            
            # Kiemeljük a javaslatot, ha megtalálható
            recommendation = desc[:70] + ("..." if len(desc) > 70 else "")
            
            # Architektúra alapján kiegészítés
            arch = m.get('architecture', {})
            if arch and isinstance(arch, dict):
                modality = arch.get('modality')
                if modality and modality != "text->text":
                    recommendation = f"[{modality}] " + recommendation

            print(f"{display_id:<45} | {str(context):<8} | {has_tools:<6} | {str(cutoff):<10} | {recommendation}")

        print("-" * 120)
        print(f"Összesen {len(free_models)} ingyenes modellt találtam.")

    except Exception as e:
        print(f"Hiba történt a lekérdezés során: {e}")

if __name__ == "__main__":
    print("OpenRouter Ingyenes Modellek:")
    get_free_openrouter_models()
    print("\n---\n")
    print("Groq Ingyenes Modellek:")
    get_free_groq_models()
    print("\n---\n")