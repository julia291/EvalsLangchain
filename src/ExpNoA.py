from validations import rule
from agent import ChallengeEnv


def ExpNoDefault(): 
    
    flagtype: str = "r_whole"  # ["r_name", "r_domain", "r_tld", "r_whole"]
    rel_flagsize: float = 0.1  # Anteil der Empfänger, die als verdächtig markiert werden

    # 2. Umgebung initialisieren
    # Wir laden direkt die mails.json
    env = ChallengeEnv(mails_path="data/mails.json", flagtype=flagtype, rel_flagsize=rel_flagsize)

    if not env.mails:
        logger.error("Keine E-Mails gefunden. Abbruch.")
        return

    # 3. Agenten erstellen
    try:
        agent = env.create_agent_runner(api_key=OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Agenten: {e}")
        return

    # 4. Iteration durch die E-Mails
    print(f"\n--- MISSION START --- {len(env.mails)} E-Mails zu bearbeiten.\n")

    pass
    

