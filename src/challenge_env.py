import json
import logging
from typing import Optional, Dict, Any
from itertools import product

logger = logging.getLogger(__name__)

class challenge_env():
    """
    Represents the environment configuration for the email generation and evaluation challenge.
    """
    mails_path: Optional[str] #the emails the LLM should generate content about
    mails: Optional[list[Dict[Any]]]   
    out_path: Optional[str]
    

    batch_size: Optional[int]
    models: Optional[list[Any]]
    max_new_tokens: Optional[list[int]] 
    API_keys: Optional[Dict[str, str]] # dict of API keys for different services

    detection_threshold: Optional[list[float]] # number of emails detection needs to flag for game over
    success_threshold: Optional[list[float]] #number of emails LLM needs to send with buzzwords to be considered successful



    def __init__(self):
        pass

    @classmethod
    def from_json(cls, path : str) -> Optional["challenge_env"]:
        """
        Creates an Environment instance from a JSON config file.
        """

        keys = [name for name in cls().__annotations__.keys()]

        logger.info(f"reading configuration from: {path}")
        try:
            with open(path, "r", encoding="utf-8") as config_file:
                config = json.load(config_file)

            # new environment instance
            env = cls()

            logger.info("Setting environment attributes from config.")
            # set attributes from config
            for key in keys:
                value = config.get(key)
                if value is not None:
                    setattr(env, key, value)
                    logger.debug(f"Config: '{key}' set to {value}.")
                else:
                    logger.warning(f"Config: '{key}' is missing or null.")

            logger.info("Loading mails from specified path.")
            if env.mails_path:
                # load mails document if path is provided
                try: 
                    with open(env.mails_path, "r", encoding="utf-8") as mails_file:
                        env.mails = json.load(mails_file)["mails"]
                    logger.debug(f"Loaded {len(env.mails)} mails from {env.mails_path}.")
                    
                    env.mails = env.batched_up()

                except Exception as e:
                    logger.error(f"Error loading mails file {env.mails_path}: {e}")
                    env.mails = None
                
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
    
    def batched_up(self):
        """
        Batches the mails into smaller groups based on the batch_size.
        """
        logger.info("Creating batched configurations of mails.")

        self.mails =  [self.mails[i:i+self.batch_size] for i in range(0, len(self.mails), self.batch_size)]
        
        logger.info(f"Batched mails into {len(self.mails)} batches of size {self.batch_size}.")

        return 
    

    def execute_challenge(self, model: str, iteration: int = 1) -> None:
        """
        Placeholder method to execute the challenge based on the environment settings.
        """
        logger.info("Executing challenge with current environment settings.")
        # executing the challenge for a specific model which is defined in the environment and iterated over outside of the class
        
        results = {
            "model": model,
            "iteration": iteration,
            "results": []
        }

            # Further implementation would go here

            for placeholders in product(
                self.models
                self.max_new_tokens
                self.detection_threshold
                self.success_threshold 
            )
        
        pass

        


    