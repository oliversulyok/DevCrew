import os
import re
import json
from datetime import datetime

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
        
        # 1. Próba: A kódblokk legelső sorában van-e egy fájlnév?
        first_line = content.split('\n')[0].strip()
        fname_match = re.match(r'^(?:#|//|\*)?\s*([a-zA-Z0-9_/\-.]+\.(?:json|md|py))\s*(?:\*)?$', first_line)
        if fname_match:
            filename = fname_match.group(1)
            content = '\n'.join(content.split('\n')[1:]).strip()
        
        # 2. Próba: Kódblokk előtti szöveg
        if not filename:
            pre_text = eredmeny[:match.start()].strip()
            pre_text_lines = pre_text.split('\n')
            if pre_text_lines:
                last_line = pre_text_lines[-1].strip()
                last_line_match = re.search(r'([a-zA-Z0-9_/\-.]+\.(?:json|md|py))(?:\s|$|:|\*|`)', last_line)
                if last_line_match:
                    filename = last_line_match.group(1)
        
        if not filename:
            if last_known_filename:
                filename = last_known_filename
            else:
                ext = lang if lang in ['json', 'md', 'py'] else 'py'
                filename = f"generated_output_{found_files+1}.{ext}"

        last_known_filename = filename
        file_path = os.path.join(project_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
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
    """Menti az állapotot a summary.json-ba."""
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
