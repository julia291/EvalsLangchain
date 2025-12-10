import json
import logging

logger = logging.getLogger(__name__)

class Environment():

    def __init__(self):
        self.mails_path: str  | None = None #the emails the LLM should generate content about 
        self.mails_doc:  dict | None = None 

        self.out_path:   str  | None = None
        self.out_doc:    dict | None = None

        self.batch_size: int  | None = None

    @classmethod
    def from_json(cls, path : str) -> "Environment  | None":
        """
        Creates an Environment instance from a JSON config file.
        """
        logger.info(f"reading configuration from: {path}")
       
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # neues Environment-Objekt
            env = cls()

            # Felder aus config übernehmen (falls sie existieren)
            env.mails_path = config.get("mails_path")
            env.out_path = config.get("out_path")
            env.batch_size = config.get("batch_size")

            logger.debug(f"Config geladen: {config}")

            logger.info("Environment erfolgreich erstellt.")

            return env
        
        except FileNotFoundError:
            logger.error(f"Config file not found: {path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"malformed JSON in file {path}: {e}")
            return None
        
        
    
        

env = Environment.from_json(path = r"data\specs_data_beispiel.json" )

print(env)


        


    