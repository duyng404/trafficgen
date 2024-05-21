
import argparse
import pprint
from trafficgen.emulator import AndroidEmulator

def main(emulator: AndroidEmulator, *args):
	"""A simple and handy experiment used to interact with the emulator during development. Not a real experiment.

	Usage: run `python trafficgen interact dump` (replace dump with any other action)
	"""
	parser = argparse.ArgumentParser(description='Interact with the running emulator.')
	parser.add_argument('action', help='Name of the action', nargs='?', default="dump")
	parser.add_argument('options', help='Options of the action', nargs='*', default=[])

	args = parser.parse_args(args)

	action = args.action
	options = args.options

	if action == "dump":
		emulator.interactor.dumpActions()

	if action == "dump-text":
		emulator.interactor.dumpTexts()

	if action == "click":
		emulator.interactor.clickOnButtonName(options[0])

	if action == "click-coord":
		emulator.interactor.clickOnCoordinate(int(options[0]), int(options[1]))

	if action == "click-random":
		emulator.interactor.clickOnRandomButtonName(options[0])

	if action == "type":
		emulator.interactor.typeInputText(options[0])

	if action == "scroll-down":
		emulator.interactor.scrollDownHalfPage()

	if action == "scroll-down-long":
		emulator.interactor.scrollDownFullPage()

	if action == "scroll-up":
		emulator.interactor.scrollUpHalfPage()

	if action == "install-apk":
		emulator.installApk(options[0])

	if action == "home-button":
		emulator.interactor.homeButton()

	if action == "recent-button":
		emulator.interactor.recentAppButton()

	if action == "open-app":
		emulator.openApp(options[0])
