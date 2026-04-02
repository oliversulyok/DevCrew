from crewai import Agent
from dev_crew.app.config.models import architekt_llm, kodolo_llm, olcso_llm

def define_agents():
    """Létrehozza a munkában résztvevő ágenseket."""
    po = Agent(
        role=f'Product Owner ({architekt_llm.model_name})',
        goal='Prioritizáld a feladatokat és válaszd ki a megfelelő végrehajtót.',
        backstory='Tapasztalt vezető vagy, aki ügyel a kvótákra és az üzleti célokra.',
        llm=architekt_llm,
        verbose=True,
        max_rpm=3
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
        max_rpm=2
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
