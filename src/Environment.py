import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class Environment():

    def __init__(self):
        self.mails_path: Optional[str] = None #the emails the LLM should generate content about 
        self.mails_doc:  Optional[Dict[str, Any]] = None 

        self.out_path:   Optional[str] = None
        self.out_doc:    Optional[Dict[str, Any]] = None # not yet used, maybe for future extensions

        self.batch_size: Optional[str] = None
        self.models:     Optional[list[Any]] = None # list of model names or classes to use
        self.max_new_tokens: Optional[list[int]] = None
        self.API_keys:  Optional[Dict[str, str]] = None # dict of API keys for different services

    @classmethod
    def from_json(cls, path : str) -> Optional["Environment"]:
        """
        Creates an Environment instance from a JSON config file.
        """

        keys = ["mails_path", "out_path", "batch_size", "models", "max_new_tokens", "API_keys"]

        logger.info(f"reading configuration from: {path}")
       
        try:
            with open(path, "r", encoding="utf-8") as config_file:
                config = json.load(config_file)

            # new environment instance
            env = cls()

            # set attributes from config
            for key in keys:
                value = config.get(key)

                if value is not None:
                    setattr(env, key, value)
                    logger.debug(f"Config: '{key}' set to {value}.")
                else:
                    logger.warning(f"Config: '{key}' is missing or null.")
        
           

            if env.mails_path:
                # load mails document if path is provided
                try: 
                    with open(env.mails_path, "r", encoding="utf-8") as mails_file:
                        env.mails_doc = json.load(mails_file)
                except Exception as e:
                    logger.error(f"Error loading mails file {env.mails_path}: {e}")
                    env.mails_doc = None

            else:
                logger.warning("mails_path is not set in the config.")

        
            logger.info("Environment erfolgreich erstellt.")

            return env

        except FileNotFoundError:
            logger.error(f"Config file not found: {path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"malformed JSON in file {path}: {e}")
            return None
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Environment instance to a dictionary.
        """
        logger.info("Converting Environment to dictionary.")

        return {
            "mails_path": self.mails_path,
            "out_path": self.out_path,
            "batch_size": self.batch_size,
            "models": self.models,
            "max_new_tokens": self.max_new_tokens,
            "API_keys": self.API_keys
            }
    

    def to_json(self, json_str: str,  path: Optional[str] = None) -> None:
        """
        Saves the Environment instance to a JSON file.
        """
        logger.info(f"Saving Environment to JSON file: {path if path else self.out_path}")
    
        if path is None:
            path = self.out_path
        assert(path is not None)

        #with open(path, "w", encoding="utf-8") as out_file: #for future use
            
        logger.info("PLACEHOLDER successfully saved to JSON.")

        pass
    
    def execute_challenge(self):
        """
        Placeholder method to execute the challenge based on the environment settings.
        """
        logger.info("Executing challenge with current environment settings.")
        # Implementation would go here
        pass





        


    