import random
from math import ceil

def random_whole_flags(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects names from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flags.add(mail.get("recipient").lower())
    
    subset_size = ceil(rel_size * len(flags)) 
    return random.sample(list(flags), min(subset_size, len(flags)))

def random_name_flags(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
            flag = mail.get("recipient").split("@", 1)[0].lower()
            flags.add(flag)

    subset_size = ceil(rel_size * len(flags)) 
    return random.sample(list(flags), min(subset_size, len(flags)))

def random_domain_flags(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()
    
    for mail in mails:
            flag = mail.get("recipient").split("@", 1)[1].lower()
            flags.add(flag)

    subset_size = ceil(rel_size * len(flags)) 

    return random.sample(list(flags), min(subset_size, len(flags)))

def random_tld_flags(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flag= mail.get("recipient").split("@", 1)[1].lower().split(".")[-1]
        flags.add(flag)

    subset_size = ceil(rel_size * len(flags)) 
    return random.sample(list(flags), min(subset_size, len(flags)))
  