import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# 1. Környezet beállítása
load_dotenv()
os.makedirs("project_state", exist_ok=True)
print(os.getcwd())

# --- MODELL DEFINÍCIÓK ---

# ARCHITEKTÚRA ÉS PO (Groq - Villámgyors Llama 3 70B)
# Ideális döntéshozatalhoz és tervezéshez
architekt_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model_name="openrouter/qwen/qwen3.6-plus-preview:free",
    max_retries=10, # Több újrapróbálkozás hálózati hiba vagy limit esetén
)

# KÓDOLÁS ÉS TRIAGE 
# (OpenRouter - DeepSeek R1 volt az ajánlott, de GPT-OSS-120B is ingyenes és erős lehet)
kodolo_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openrouter/stepfun/step-3.5-flash:free",
    max_retries=10,
)

# EGYSZERŰ FELADATOK (OpenRouter - Ingyenes modellek)
# pl. Prompt optimalizálás
olcso_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openrouter/nvidia/nemotron-3-nano-30b-a3b:free", # Példa ingyenes modellre
    max_retries=10,
)

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
    
    # SDD mappastruktúra inicializálása
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "spec"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "test"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "docs"), exist_ok=True)
    
    return projekt_cel, is_rc, project_dir

def check_specifications(project_dir):
    """Listázza a meglévő specifikációkat és rákérdez a fejlesztés indítására."""
    spec_dir = os.path.join(project_dir, "docs")
    print("\n--- Jelenlegi specifikációk ---")
    
    spec_files = []
    if os.path.exists(spec_dir):
        for root, _, files in os.walk(spec_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                spec_files.append(rel_path)
                
    if not spec_files:
        print(" Nincsenek még specifikációk a 'docs' mappában (Most fognak generálódni).")
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

def load_last_context(project_dir):
    """Beolvassa a generált fájlok tartalmát a spec, src, test (stb.) mappákból."""
    context = "\n--- JELENLEGI FÁJLOK TARTALMA ---\n"
    found_files = False
    
    target_dirs = ["spec", "src", "test", "docs"]
    
    for dir_name in target_dirs:
        dir_path = os.path.join(project_dir, dir_name)
        if os.path.exists(dir_path):
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    found_files = True
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, project_dir)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                            context += f"\nFájl: {rel_path}\nTartalom:\n```\n{content}\n```\n"
                    except:
                        pass
    
    return context if found_files else ""

def define_agents():
    """Létrehozza a munkában résztvevő ágenseket."""
    po = Agent(
        role=f'Product Owner ({architekt_llm.model_name})',
        goal='Prioritizáld a feladatokat és válaszd ki a megfelelő végrehajtót.',
        backstory='Tapasztalt vezető vagy, aki ügyel a kvótákra és az üzleti célokra.',
        llm=architekt_llm,
        verbose=True,
        max_rpm=3 # Kérés/perc korlát az OpenRouter ingyenes limitjeihez igazítva
    )

    prompt_eng = Agent(
        role=f'Prompt Optimalizáló ({olcso_llm.model_name})',
        goal='Minimalizáld a feladatleírások token-számát a lényeg megtartásával.',
        backstory='A minimalizmus nagymestere vagy. Technikai, tömör utasításokat gyártasz.',
        llm=olcso_llm,
        verbose=True,
        max_rpm=5
    )

    dev = Agent(
        role=f'Senior Python Fejlesztő ({kodolo_llm.model})',
        goal='Írj tiszta, működő kódot az eredeti cél és a prompt alapján.',
        backstory='Profi kódoló vagy, aki követi a best practice-eket.',
        llm=kodolo_llm,
        verbose=True,
        max_rpm=2 # A nagy modellek OpenRouter-en gyakran szigorúbb korlátúak
    )

    qa = Agent(
        role=f'QA Mérnök ({kodolo_llm.model})',
        goal='Teszteld a kódot (Unit, E2E, UAT) és keress hibákat.',
        backstory='Alapos és szigorú vagy. Csak a tökéletes kód mehet át.',
        llm=kodolo_llm,
        verbose=True,
        max_rpm=2
    )

    triage = Agent(
        role=f'Triage Specialista ({kodolo_llm.model})',
        goal='Hiba esetén döntsd el: kódjavítás vagy tesztkorrekció kell.',
        backstory='Rendszerszintű elemző vagy, aki megakadályozza a felejtést és a felesleges köröket.',
        llm=kodolo_llm,
        verbose=True,
        max_rpm=3
    )

    security = Agent(
        role=f'Biztonsági Auditor ({kodolo_llm.model})',
        goal='Sérülékenységvizsgálat és biztonsági jóváhagyás.',
        backstory='Etikus hacker vagy, aki az utolsó védelmi vonalat jelenti.',
        llm=kodolo_llm,
        verbose=True,
        max_rpm=2
    )
    
    return {"po": po, "prompt_eng": prompt_eng, "dev": dev, "qa": qa, "triage": triage, "security": security}

def create_tasks(agents, projekt_cel, is_rc, extra_context="", run_dev=False):
    """Láncba fűzi a feladatokat."""
    full_description = f"{projekt_cel}\n\n{extra_context}" if extra_context else projekt_cel
    
    task_original = Task(
        description=f"Projekt cél és kontextus rögzítése: {full_description}\nHozz létre vagy frissíts több, logikailag szétválasztott részletes üzleti specifikációt (pl. architektura, frontend, backend, adatbazis) mardown vagy json formátumban a 'docs/' mappába. Kifejezetten kerüld el, hogy mindent egyetlen fájlba zsúfolj!",
        expected_output="Több különálló specifikációs dokumentum. A kimenetben minden fájlnál jelezd a fájlnevet pl. `docs/architektura.md`, `docs/adatbazis.json` formában.",
        agent=agents["po"]
    )

    task_optimize = Task(
        description="Alakítsd át az összes kapott projekt specifikációt külön-külön a lehető legrövidebb technikai prompttá. Ezeket technikai specifikációként (json vagy md) mentsd a 'spec/' mappába, megtartva a felosztást.",
        expected_output="A specifikációk megfelelő optimalizált párjai. Mellékeld a kódblokkokat pl. `spec/architektura.json` formában.",
        agent=agents["prompt_eng"],
        context=[task_original]
    )

    tasks_list = [task_original, task_optimize]

    if run_dev:
        task_dev = Task(
            description="Írd meg vagy javítsd a szoftvert az optimalizált prompt alapján. A forráskódot 'src/', az egyéb fájlokat a megfelelő mappába tedd.",
            expected_output="A szoftver teljes forráskódja.",
            agent=agents["dev"],
            context=[task_optimize, task_original]
        )
        tasks_list.append(task_dev)

        if is_rc:
            task_qa = Task(
                description="Végezz Unit, E2E és UAT teszteket a kapott kódon. A teszt kódokat és riportokat tedd a 'test/' könyvtárba.",
                expected_output="Tesztriport (PASS vagy hibalista).",
                agent=agents["qa"],
                context=[task_dev, task_original]
            )
            tasks_list.append(task_qa)
            task_security = Task(
                description="Végezz mély biztonsági auditot (OWASP, Injection, Secrets). A jelentést a 'docs/' mappába tedd.",
                expected_output="Biztonsági tanúsítvány vagy javítandó pontok.",
                agent=agents["security"],
                context=[task_dev]
            )
            tasks_list.append(task_security)
    return tasks_list

def execute_agency(agents, tasks_list):
    """Végrehajtja a feladatokat."""
    print("\n--- Aktív Ügynökök és Modellek ---")
    for task in tasks_list:
        print(f" - {task.agent.role}")

    print("\n--- Munkafolyamat indul... ---")
    
    final_results = []

    for i, task in enumerate(tasks_list):
        print(f"\n🚀 {task.agent.role} dolgozik...")
        temp_crew = Crew(agents=[task.agent], tasks=[task], verbose=False)
        
        result = temp_crew.kickoff()
        result_str = str(result)
        final_results.append(result_str)
        
        if i < len(tasks_list) - 1:
            valasz = input(f"\n✅ A(z) '{task.agent.role}' ágens végzett. Kérlek nézd át az addigi logokat!\nSzeretnéd folytatni a szakaszokat? (y/n) [y]: ").lower()
            if valasz == 'n':
                print("🛑 Folyamat megszakítva a felhasználó által! A meglevő eredmények mentésre kerülnek.")
                break

    return "\n\n".join(final_results)

def save_files(project_dir, eredmeny):
    """Fájlok kimentése a generált szövegből."""
    print("\n--- Fájlok generálása... ---")
    
    blocks = re.finditer(r'```([a-zA-Z0-9\+\-\s]*)\n(.*?)\n\s*```', eredmeny, re.DOTALL)
    
    saved_files_list = []
    found_files = 0
    last_known_filename = None
    written_files = set()

    for match in blocks:
        lang = match.group(1).strip().lower()
        content = match.group(2).strip()
        filename = None
        
        # 1. Próba: A kódblokk legelső sorában van-e egy fájlnév (esetleg # vagy // után)?
        first_line = content.split('\n')[0].strip()
        fname_match = re.match(r'^(?:#|//|\*)?\s*([a-zA-Z0-9_/\-.]+\.(?:json|md|py))\s*(?:\*)?$', first_line)
        if fname_match:
            filename = fname_match.group(1)
            # Levágjuk az első sort a tartalomról
            content = '\n'.join(content.split('\n')[1:]).strip()
        
        # 2. Próba: A kódblokk előtti szövegben van-e valami fájlnév formátum?
        if not filename:
            pre_text = eredmeny[:match.start()].strip()
            pre_text_lines = pre_text.split('\n')
            if pre_text_lines:
                last_line = pre_text_lines[-1].strip()
                last_line_match = re.search(r'([a-zA-Z0-9_/\-.]+\.(?:json|md|py))(?:\s|$|:|\*|`)', last_line)
                if last_line_match:
                    filename = last_line_match.group(1)
        
        # 3. Auto-név generálás (csak ha korábban se volt ismert fájlnév)
        if not filename:
            if last_known_filename:
                filename = last_known_filename
            else:
                ext = lang if lang in ['json', 'md', 'py'] else 'py'
                filename = f"generated_output_{found_files+1}.{ext}"

        last_known_filename = filename

        file_path = os.path.join(project_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Markdown esetén érdemes hozzáfűzni, egyébként elsőre felülírni
        mode = "a" if filename in written_files else "w"
        
        with open(file_path, mode, encoding="utf-8") as f:
            if mode == "a":
                f.write('\n\n' + content + '\n')
            else:
                f.write(content + '\n')
                
        written_files.add(filename)
        
        if filename not in saved_files_list:
            print(f" 💾 Mentve: {filename}")
            saved_files_list.append(filename)
            
        found_files += 1

    if found_files == 0:
        print(" ⚠️ Nem találtam kódblokkot az eredményben.")
        
    return saved_files_list

def save_state(project_dir, projekt_cel, is_rc, saved_files):
    """Menti az állapotot a summary.json-ba (iteratív módon)."""
    summary_path = os.path.join(project_dir, "summary.json")
    
    iterations = []
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                iterations = data if isinstance(data, list) else [data]
        except:
            pass

    new_iteration = {
        "timestamp": datetime.now().isoformat(),
        "projekt": projekt_cel,
        "is_rc": is_rc,
        "modositott_fajlok": saved_files
    }
    iterations.append(new_iteration)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(iterations, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Iteratív állapot elmentve: {summary_path}")

def run_ai_agency():
    """Fő vezérlő folyamat."""
    projekt_cel, is_rc, project_dir = get_project_config()
    
    while True:
        choice = check_specifications(project_dir)
        
        if choice == 'q':
            print("👋 Viszlát!")
            break
            
        run_dev = (choice == 'y')
        
        # Ha iterációt kértek, kérünk be extra visszajelzést
        if choice == 'i':
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
                
                # Próbáljuk kitalálni a kontextust (melyik fájlhoz tartozik)
                context_tag = ""
                fb_lower = fb.lower()
                for f in available_files:
                    fname_base = f.split('.')[0].lower()
                    # Ha a fájlnév szerepel a szövegben vagy a visszajelzés elején van : jel után
                    if fname_base in fb_lower:
                        context_tag = f" [Kontextus: docs/{f}]"
                        break
                
                feedbacks.append(f"{context_tag} {fb}")
            
            if feedbacks:
                feedback_str = "\n".join(feedbacks)
                projekt_cel += f"\n\n--- FELHASZNÁLÓI VISSZAJELZÉS (Iteráció - {datetime.now().strftime('%H:%M:%S')}) ---\n{feedback_str}"
                
                # Mentés az állapotba is
                last_goal_path = "project_state/last_goal.txt"
                with open(last_goal_path, "w", encoding="utf-8") as f:
                    f.write(projekt_cel)
            else:
                print("ℹ️ Nem érkezett visszajelzés, folytatás vátloztatás nélkül.")

        # Utolsó állapot betöltése kontextusnak
        extra_context = load_last_context(project_dir)
        if extra_context:
            print("ℹ️ Korábbi kontextus betöltve az ágensek részére.")

        agents = define_agents()
        tasks_list = create_tasks(agents, projekt_cel, is_rc, extra_context, run_dev)
        
        eredmeny = execute_agency(agents, tasks_list)
        
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