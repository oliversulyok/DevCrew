import os
from utils.ui import get_project_config, check_specifications, collect_iterative_feedback
from utils.file_io import load_last_context, save_files, save_state
from agents.factory import define_agents
from tasks.workflow import create_tasks, execute_agency
from utils.vector_store import sync_project_files, get_chroma_db

def run_ai_agency():
    """Fő vezérlő folyamat."""
    projekt_cel, is_rc, project_dir = get_project_config()
    
    while True:
        choice = check_specifications(project_dir)
        
        if choice == 'q':
            print("👋 Viszlát!")
            break
            
        run_dev = (choice == 'y')
        
        if choice == 'i':
            projekt_cel = collect_iterative_feedback(project_dir, projekt_cel)

        # Szinkronizáció és kontextus betöltése a vektor-adatbázisból
        sync_project_files(project_dir)
        extra_context = ""
        try:
            db = get_chroma_db(project_dir)
            # Lekérjük a leginkább releváns dokumentumrészleteket a cél alapján
            relevant_docs = db.similarity_search(projekt_cel, k=4)
            if relevant_docs:
                extra_context = "\n--- RELEVÁNS KONTEXTUS (Vektor-adatbázisból) ---\n"
                for d in relevant_docs:
                    extra_context += f"\nFájl: {d.metadata.get('source', 'ismeretlen')}\nTartalom:\n```\n{d.page_content}\n```\n"
                print("ℹ️ Releváns kontextus betöltve az ágensek részére.")
        except Exception as e:
            print(f"⚠️ Hiba a vektoros keresés során: {e}. Üres kontextussal indulunk.")

        # Ügynökök és folyamatok
        agents = define_agents(project_dir)
        tasks_list = create_tasks(agents, projekt_cel, is_rc, extra_context, run_dev)
        
        # Végrehajtás
        eredmeny = execute_agency(agents, tasks_list)
        
        # Mentés
        saved_files = save_files(project_dir, eredmeny)
        # Szinkronizáció a generált fájlok mentése után, hogy a DB frissüljön
        sync_project_files(project_dir)
        
        save_state(project_dir, projekt_cel, is_rc, saved_files)
        
        if run_dev:
            print("\n🎉 Fejlesztési szakasz befejeződött.")
            break
        else:
            print("\n✅ Specifikációs kör kész. Most átnézheted a fájlokat, majd újabb kört indíthatsz vagy mehet a fejlesztés.")

if __name__ == "__main__":
    try:
        run_ai_agency()
    except Exception as e:
        print(f"\n❌ Hiba történt: {e}")
        # Nyomkövetéshez (opcionális):
        # import traceback; traceback.print_exc()