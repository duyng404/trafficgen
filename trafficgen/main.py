import sys
import argparse
import traceback
import yaml
import logging
from importlib import import_module
from emulator import AndroidEmulator
import utils

def read_yaml_config(file_path: str) -> dict[str, any]:
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def setup_logging(debug_mode: bool) -> None:
    level = logging.DEBUG
    if not debug_mode:
        level = logging.INFO
    # Create a basic configuration for logging
    logging.basicConfig(
        level=level,  # Set to the minimum level you want to handle globally
        format='[%(levelname)s] %(filename)s:%(lineno)d %(message)s'
    )

def main():
    # sets up and parse arguments
    parser = argparse.ArgumentParser(description="Generate traffic in android emulator and capture them into pcap files.")
    parser.add_argument('experiment', help='Name of the experiment to execute', nargs='?', default="randomapp")
    parser.add_argument('-c', '--config', help='Config file, must be in yaml/yml format', default="config.yaml")
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments for the experiment if any', default=[])

    args = parser.parse_args()
    experiment_name = args.experiment
    config_file = args.config
    experiment_args = args.args

    # read config
    config = read_yaml_config(config_file)
    setup_logging(config["debug_mode"])
    utils.setup_utils(config["debug_mode"])
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded config file: {config_file}")

    # import experiment code
    try:
        logger.info(f"Running experiment {experiment_name}")
        experiment_module = import_module(f"experiments.{experiment_name}")
    except ImportError as e:
        logger.error(f"Error: Failed to import experiment {experiment_name}")
        logger.error(e)
        traceback.print_exc()
        sys.exit(1)

    # sets up emulator
    emu = AndroidEmulator(config)

	# call the experiment code
    if hasattr(experiment_module, 'main'):
        experiment_module.main(emu, *experiment_args)
    else:
        logger.error(f"Error: Experiment {experiment_name} does not have a main function")
        sys.exit(1)
