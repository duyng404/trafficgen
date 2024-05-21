
import os
import random
import threading
import time
import traceback
from trafficgen import utils
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction, ExecTimeout, ExperimentFail, ShellExecFail
from trafficgen.interactor import InteractionAction

import logging
logger = logging.getLogger(__name__)

class VpnApp:
	def __init__(self, name:str, hash:str, path:str, packagename:str, mainactivity:str):
		self.name = name
		self.hash = hash
		self.path = path
		self.packageName = packagename
		self.mainActivity = mainactivity
		self.visited = False

class ExperimentRunner:
	def __init__(self, emulator:AndroidEmulator, do_init: bool, existing_emulator: bool):
		self.emulator = emulator
		self.do_init = do_init
		self.existing_emulator = existing_emulator
		self.config = emulator.config
		self.vpnapps: list[VpnApp] = []

	def getNextMilestone(self) -> float:
		# low: 2-4 websites per 10 minutes
		noFasterThan = 130.0
		noSlowerThan = 400.0
		# medium: 4-7 websites per 10 minutes
		if self.config["randombrowse"]["websites_frequency_profile"] == "medium":
			noFasterThan = 90.0
			noSlowerThan = 200.0
		# high: 7-12 websites per 10 minutes
		if self.config["randombrowse"]["websites_frequency_profile"] == "high":
			noFasterThan = 40.0
			noSlowerThan = 120.0
		if self.config["randombrowse"]["websites_frequency_profile"] == "dev":
			return 50.0
		return random.uniform(noFasterThan, noSlowerThan)

	def readListOfApks(self):
		filepath = "trafficgen/experiments/randomvpn/apks_to_run.csv"
		fullpath = os.path.join(os.getcwd(), filepath)
		if not os.path.isfile(fullpath):
			raise ExperimentFail(f"unable to find list of apks")
		with open(fullpath, 'r') as f:
			for line in f.readlines():
				app_info = line.rstrip().split(";")
				vpnname = app_info[0] # Proxy/VPN service name
				apkhash = app_info[1].split("/")[2].split("##")[1].strip(".apk") # APK file hash
				apkpath = app_info[1] # path to apk file
				if apkpath.startswith("/"):
					apkpath = apkpath[1:]
				apkfullpath = os.path.join(os.getcwd(), "trafficgen/experiments/randomvpn/", apkpath)
				if not os.path.isfile(apkfullpath):
					print(f"APK file not available at path: {apkfullpath}")
					print("Skipping execution for this APK....")
					continue
				pkg = app_info[2]     # android package name for apk file
				mainactivity = app_info[3] # apk main/launch activity name
				self.vpnapps.append(VpnApp(
					name=vpnname,
					hash=apkhash,
					path=apkfullpath,
					packagename=pkg,
					mainactivity=mainactivity,
				))
		logger.info(f"there are {len(self.vpnapps)} vpn apps")

	def getARandomVpnApp(self) -> VpnApp:
		while True:
			choice = random.choice(self.vpnapps)
			if not choice.visited:
				return choice

	def checkForSpecialInteractions(self, vpnapp: VpnApp) -> bool:
		if vpnapp.packageName == "com.leo.appmaster":
			actions, texts = self.emulator.interactor.getActionsAndTexts(stuckFactor=0)
			if "change to pin code" in actions and "to keep from snoopers!" in texts:
				actions["change to pin code"].touch()
				time.sleep(5)
				actions, texts = self.emulator.interactor.getActionsAndTexts(stuckFactor=0)
				actions["1"].touch()
				actions["1"].touch()
				actions["1"].touch()
				actions["1"].touch()
				actions["enter"].touch()
				actions["1"].touch()
				actions["1"].touch()
				actions["1"].touch()
				actions["1"].touch()
				actions["enter"].touch()
				time.sleep(5)
				self.emulator.interactor.clickOnCoordinate(87,382) # cancel fingerprint prompt
				time.sleep(5)
				# lucky number
				self.emulator.interactor.typeInputText("1111")
				self.emulator.interactor.enterKey()
				self.emulator.interactor.clickOnButtonName("ok")
				time.sleep(5)
				# give access to applock
				self.emulator.interactor.clickOnCoordinate(160, 380) # click on give access
				time.sleep(5)
				self.emulator.interactor.clickOnCoordinate(160, 316) # click on got it
				time.sleep(2)
				actions, texts = self.emulator.interactor.getActionsAndTexts(stuckFactor=0)
				if "google play services" not in texts and "google" not in texts:
					return True
				self.emulator.interactor.clickOnCoordinate(160, 120)
				time.sleep(1)
				self.emulator.interactor.clickOnButtonName("widgetswitch0")
				time.sleep(3)
				# update
				self.emulator.interactor.clickOnCoordinate(160, 440)
				time.sleep(10)
				self.emulator.interactor.clickOnCoordinate(87,382360) # cancel ad
				return True
		if vpnapp.packageName == "com.kingroot.kinguser":
			actions, texts = self.emulator.interactor.getActionsAndTexts(stuckFactor=0)
			if "simple" in texts and "root is easier and faster" in texts:
				self.emulator.interactor.scrollDownShortFlick()
				time.sleep(1)
				self.emulator.interactor.scrollDownShortFlick()
				time.sleep(1)
				self.emulator.interactor.clickOnButtonName("try it")
				return True
			if "try to root" in actions:
				actions["try to root"].touch()
				return True
		return False

	def checkForClickableKeywords(self, vpnapp: VpnApp, actions: dict[str, InteractionAction]) -> bool:
		clickableKeywords: list[str] = [
			"start",
			"enter",
			"start using the app",
			"i agree",
			"ok",
			"skip",
			"allow",
			"connect",
			"continue",
			"add",
			"next",
			"agree",
			"got it",
			"yes",
			"start using the app",
			"off",
			"i got it",
			"always",
			"agree & continue",
			"no thanks",
			"retry",
			"while using the app",
			"only this time",
			"change to pin code",
			"yes i am 18+",
			"never scanned",
			"closeboxsign",
		]
		for action in actions:
			if action in clickableKeywords:
				actions[action].touch()
				return True
		return False

	def checkForOtherKeywords(self, vpnapp: VpnApp, actions: dict[str, InteractionAction], texts: list[str]) -> bool:
		if "close app" in actions and "wait" in actions:
			actions["close app"].touch()
			self.emulator.interactor.waitRandom(1,3)
			return True
		if "check for update" in actions and "ok" in actions and "private zone" in texts:
			actions["ok"].touch()
			self.emulator.interactor.waitRandom(1,3)
			return True
		if "lock to keep app records safe!" in texts and "tap to lock (5)" in actions and "skip" in actions:
			actions["skip"].touch()
			self.emulator.interactor.waitRandom(1,3)
			return True
		if "com.leo.appmaster:id/tv_1_top" in actions and "com.leo.appmaster:id/tv_2_top" in actions:
			actions["com.leo.appmaster:id/tv_1_top"].touch()
			actions["com.leo.appmaster:id/tv_1_top"].touch()
			actions["com.leo.appmaster:id/tv_1_top"].touch()
			actions["com.leo.appmaster:id/tv_1_top"].touch()
			self.emulator.interactor.waitRandom(1,3)
			return True
		if "install now" in texts and "android.widget.textview" in actions:
			actions["android.widget.textview"].touch()
			self.emulator.interactor.waitRandom(1,3)
			return True
		if "how to root" in actions:
			self.emulator.interactor.backButton()
			self.emulator.interactor.waitRandom(1,3)
			return True
		if "install shortcut to your desktop?" in texts and "no" in actions:
			actions["no"].touch()
			self.emulator.interactor.waitRandom(1,3)
			return True
		return False

	def performInteraction(self, vpnapp: VpnApp) -> None:
		while True:
			try:
				interacted:bool = False
				interacted = self.checkForSpecialInteractions(vpnapp)
				actions, texts = self.emulator.interactor.getActionsAndTexts(stuckFactor=0)
				if not interacted:
					interacted = self.checkForClickableKeywords(vpnapp, actions)
				if not interacted:
					interacted = self.checkForOtherKeywords(vpnapp, actions, texts)
				if not interacted:
					self.emulator.interactor.waitRandom()
				self.emulator.interactor.resetStuckCounter()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")

	def runExperiment(self):
		try:
			# inits
			self.readListOfApks()
			timeLimit = utils.randomizeTimeLimit(self.config["randomvpn"]["time_limit_per_app"] * 60) # in seconds
			events = [self.emulator.interactor.timeoutEvent]
			appsExecuted = 0

			# start the main loop
			while True:
				# choose a random app
				vpnapp = self.getARandomVpnApp()

				# start emulator
				self.emulator.start(wipeData=True, recordtraffic=True, pcapSuffix=f"{vpnapp.name}_{vpnapp.hash}")
				self.emulator.showTapShowPointer()
				logger.info("startup complete. waiting 20 seconds for emulator to stabilize")
				time.sleep(20)

				# install and open the app
				# retry up to 5 times, in case the emulator freezes up
				for i in range(5):
					try:
						self.emulator.installApk(os.path.join(os.getcwd(), "trafficgen/experiments/randomvpn/", vpnapp.path))
						break
					except ShellExecFail:
						continue
				else:
					raise Exception("unable to install apk")
				time.sleep(2)
				self.emulator.openApp(vpnapp.packageName, mainactivity=vpnapp.mainActivity)

				# set timers
				timer_thread = threading.Thread(target=utils.eventsTimer, args=(events, timeLimit))
				timer_thread.start()

				# do the browsing
				try:
					self.performInteraction(vpnapp)
				except ExecTimeout as e:
					logger.info("time to switch app")

				vpnapp.visited = True
				appsExecuted += 1
				timer_thread.join()
				# clear the events
				for event in events:
					event.clear()
				self.emulator.stop()
				logger.info("waiting 20 sec for emulator to stop")
				time.sleep(20)

				# exit if reached the desired number of apps executed
				if appsExecuted >= self.config["randomvpn"]["apps_per_run"]:
					logger.info("experiment completed!")
					break

		except Exception as e:
			logger.error(f"the experiment has been interrupted by an error: {e}")
			traceback.print_exc()

			if self.config["emulator"]["keep_on_after_failure"]:
				logger.info("leaving the emulator running for debugging purposes ...")
				while True:
					time.sleep(100)
