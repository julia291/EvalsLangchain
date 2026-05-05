import json

def save_responses(filename: str, responses: list) -> None:
    """ saves the agent responses to a json file """

    if responses:
        data = {
            "responses": responses
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    else:
        data = {
            "responses": [] 
        }

    return 
        
