from crewai import Task, Crew

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
