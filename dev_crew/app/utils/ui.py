import os
import re
from datetime import datetime

def get_project_config():
    """Lekéri a projekt nevét, RC állapotát és létrehozza a mappát."""
    print("\n=== AI Szoftverfejlesztő Ügynökség Indítása ===")
    
    last_goal_path = "project_state/last_goal.txt"
    last_goal = ""
    if os.path.exists(last_goal_path):
        with open(last_goal_path, "r", encoding="utf-8") as f:
            last_goal = f.read().strip()

    if last_goal:
        projekt_cel = input(f"Mi a projekt célja? [Alapértelmezett: '{last_goal}' - Nyomj Enter-t]: ")
        if not projekt_cel:
            projekt_cel = last_goal
    else:
        projekt_cel = input("Mi a projekt célja (Projekt Leírás)? ")

    # Mentés a következő alkalomra
    with open(last_goal_path, "w", encoding="utf-8") as f:
        f.write(projekt_cel)

    is_rc = input("Release Candidate (RC) állapot? (y/n) [n]: ").lower() == 'y'

    # --- PROJEKT MAPPA LÉTREHOZÁSA ---
    words = re.sub(r'[^\w\s-]', '', projekt_cel).split()
    if words:
        first_word = words[0].lower()
        initials = "".join([w[0].lower() for w in words[1:]])
        safe_name = f"{first_word}_{initials}" if initials else first_word
        safe_name = safe_name[:40]
    else:
        safe_name = "ismeretlen_projekt"
        
    project_dir = f"project_state/{safe_name}"
    
    os.makedirs(project_dir, exist_ok=True)
    for d in ["spec", "src", "test", "docs"]:
        os.makedirs(os.path.join(project_dir, d), exist_ok=True)
    
    return projekt_cel, is_rc, project_dir

def check_specifications(project_dir):
    """Listázza a meglévő specifikációkat és rákérdez a következő lépésre."""
    spec_dir = os.path.join(project_dir, "docs")
    print("\n--- Jelenlegi specifikációk ---")
    
    spec_files = []
    if os.path.exists(spec_dir):
        for root, _, files in os.walk(spec_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                spec_files.append(rel_path)
                
    if not spec_files:
        print(" Nincsenek még specifikációk a 'docs' mappában.")
    else:
        for f in spec_files:
            print(f" - {f}")

    print("\nMit tegyünk?")
    print(" [y] Mehet a fejlesztés (kódgenerálás)")
    print(" [n] Csak a specifikációk generálása / frissítése")
    print(" [i] Iteratív módosítás (Visszajelzés és újratervezés)")
    print(" [q] Kilépés")
    
    choice = input("\nVálasztás [n]: ").lower()
    if not choice: choice = 'n'
    return choice

def collect_iterative_feedback(project_dir, current_goal):
    """Begyűjti az iteratív visszajelzéseket a felhasználótól."""
    spec_dir = os.path.join(project_dir, "docs")
    available_files = []
    if os.path.exists(spec_dir):
        available_files = [f for f in os.listdir(spec_dir) if f.endswith('.md') or f.endswith('.json')]
    
    print("\n--- Iteratív visszajelzés gyűjtése ---")
    if available_files:
        print("Segítségül az eddigi fájlok:")
        for f in available_files:
            print(f" - {f}")
        print("\nTipp: Ha egy konkrét fájlhoz írsz, említsd meg a nevét (pl. 'architektura: ...')")
    
    print("Írd be a módosítási kéréseidet! (Üres sor a befejezéshez)")
    
    feedbacks = []
    while True:
        fb = input(" > ").strip()
        if not fb:
            break
        
        context_tag = ""
        fb_lower = fb.lower()
        for f in available_files:
            fname_base = f.split('.')[0].lower()
            if fname_base in fb_lower:
                context_tag = f" [Kontextus: docs/{f}]"
                break
        
        feedbacks.append(f"{context_tag} {fb}")
    
    if feedbacks:
        feedback_str = "\n".join(feedbacks)
        new_goal = current_goal + f"\n\n--- FELHASZNÁLÓI VISSZAJELZÉS (Iteráció - {datetime.now().strftime('%H:%M:%S')}) ---\n{feedback_str}"
        
        last_goal_path = "project_state/last_goal.txt"
        with open(last_goal_path, "w", encoding="utf-8") as f:
            f.write(new_goal)
        return new_goal
    
    print("ℹ️ Nem érkezett visszajelzés, folytatás vátloztatás nélkül.")
    return current_goal
