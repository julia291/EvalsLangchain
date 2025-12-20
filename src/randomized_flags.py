from math import ceil
import random

def r_whole(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects names from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        for recipient in mail.get("receipient"):
            flags.add(receipient)

    subset_size = ceil(rel_size * len(flags)) 
    return random.sample(list(flags), min(subset_size, len(flags)))

def r_name(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        for receipient in mail.get("receipient"):
                flag = receipient.split("@", 1)[0].lower()
                flags.add(flag)

    subset_size = ceil(rel_size * len(flags)) 
    return random.sample(list(flags), min(subset_size, len(flags)))

def r_domain(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()
    for mail in mails:
        for receipient in mail.get("receipient"):
                flag = receipient.split("@", 1)[1].lower()
                flags.add(flag)

    subset_size = ceil(rel_size * len(flags)) 

    return random.sample(list(flags), min(subset_size, len(flags)))

def r_tld(mails: list[dict], rel_size: int) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()
    for mail in mails:
        receipients = mail.get("receipient_domain")

        for receipient in receipients:
                flag= recipient.split("@", 1)[1].lower().split(".")[-1]
                flags.add(flag)

    subset_size = ceil(rel_size * len(flags)) 
    return random.sample(list(flags), min(subset_size, len(flags)))
 