import argparse
from trafficgen.emulator import AndroidEmulator
from trafficgen.experiments.randomapp.runner import ExperimentRunner

import logging
logger = logging.getLogger(__name__)

def main(emulator: AndroidEmulator, *args: any):
	parser = argparse.ArgumentParser(description='Experiment randomapp.')
	parser.add_argument('--init', action='store_true', help='If set, emulator will first do a separate session with -wipe-data, to install apks and setups and logins, then restart and do the actual experiment.')
	parser.add_argument('--init-only', action='store_true', help='If set, emulator will only start up and do setups, install apks and logins, then shut off without doing experiments. Will override --init.')
	args = parser.parse_args(args)

	do_init = args.init
	if do_init:
		logger.info("--init is specified, will wipe data and re-init emulator before running experiment")
	init_only = args.init_only
	if init_only:
		logger.info("--init-only is specified, will wipe data and re-init emulator without running experiment")
	if not do_init and not init_only:
		logger.info("will start emulator and run experiment without wiping data")

	runner = ExperimentRunner(emulator, do_init, init_only)
	runner.runExperiment()
