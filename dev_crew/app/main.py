import os
from dev_crew.app.utils.ui import get_project_config, check_specifications, collect_iterative_feedback
from dev_crew.app.utils.file_io import load_last_context, save_files, save_state
from dev_crew.app.agents.factory import define_agents
from dev_crew.app.tasks.workflow import create_tasks, execute_agency

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

        # Kontextus betöltése
        extra_context = load_last_context(project_dir)
        if extra_context:
            print("ℹ️ Korábbi kontextus betöltve az ágensek részére.")

        # Ügynökök és folyamatok
        agents = define_agents()
        tasks_list = create_tasks(agents, projekt_cel, is_rc, extra_context, run_dev)
        
        # Végrehajtás
        eredmeny = execute_agency(agents, tasks_list)
        
        # Mentés
        saved_files = save_files(project_dir, eredmeny)
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