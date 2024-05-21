import argparse
from trafficgen.emulator import AndroidEmulator
from trafficgen.experiments.randomvpn.runner import ExperimentRunner

import logging
logger = logging.getLogger(__name__)

def main(emulator: AndroidEmulator, *args: any):
	parser = argparse.ArgumentParser(description='Experiment randomvpn.')
	parser.add_argument('--init', action='store_true', help='If set, emulator will start up fresh with -wipe-data, and do initial chrome set up.')
	parser.add_argument('--existing-emulator', action='store_true', help='If set, will not start (nor kill) any emulators. Assuming an emulator process is already running and will only take control of it.')
	args = parser.parse_args(args)

	do_init = args.init
	if do_init:
		logger.info("--init is specified, will wipe data and re-init emulator before running experiment")
	existing_emulator = args.existing_emulator
	if existing_emulator:
		logger.info("--existing-emulator is specified, using already running emulator")
	if not do_init and not existing_emulator:
		logger.info("will start emulator normally and run experiment without wiping data")

	runner = ExperimentRunner(emulator, do_init, existing_emulator)
	runner.runExperiment()
