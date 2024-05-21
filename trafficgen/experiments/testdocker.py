
import logging
import pprint
logger = logging.getLogger(__name__)

def main(emulator: any, *args):
    logger.info("hello world")
    logger.info("emulator is:")
    print(emulator)
    logger.info("config is:")
    pprint.pprint(emulator.config)
    logger.info("if you're seeing this it means everything works!")
