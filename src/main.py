from config_logging import setup_logging
import logging


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Programm gestartet")
    logger.debug("Starte Berechnung")
    
    print("Hello from evalslangchain!")


if __name__ == "__main__":
    main()
