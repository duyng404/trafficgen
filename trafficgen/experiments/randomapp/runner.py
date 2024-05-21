

import os
import random
import threading
import time
import traceback
from trafficgen import utils
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ExecStuck, ExecUnstucked, ExecTimeout, ExperimentFail, ErrNoAction
from trafficgen.experiments.randomapp.amazon import Amazon
from trafficgen.experiments.randomapp.candycrush import CandyCrush
from trafficgen.experiments.randomapp.discord import Discord
from trafficgen.experiments.randomapp.instagram import Instagram
from trafficgen.experiments.randomapp.reddit import Reddit
from trafficgen.experiments.randomapp.spotify import Spotify
from trafficgen.experiments.randomapp.twitter import Twitter
from trafficgen.experiments.randomapp.appInteractor import AppInteractor
from trafficgen.experiments.randomapp.youtube import Youtube

import logging
logger = logging.getLogger(__name__)

class ExperimentRunner:
	def __init__(self, emulator:AndroidEmulator, do_init: bool, init_only: bool):
		self.emulator = emulator
		self.do_init = do_init
		self.init_only = init_only
		self.config = emulator.config
		self.apps: dict[str, AppInteractor] = dict()
		self.visitedApps: dict[str, bool] = dict()

	def signIntoGooglePlay(self) -> None:
		interactor = self.emulator.interactor
		interactor.clearUnblockers()
		self.emulator.openApp("com.android.vending")
		time.sleep(3)
		interactor.clickOnButtonName("sign in", retries=10)
		time.sleep(1)
		interactor.clickOnButtonName("textfield0", retries=10)
		interactor.typeInputText(self.config["google_account"]["email"])
		interactor.clickOnButtonName("next")
		time.sleep(2)
		interactor.clickOnButtonName("textfield0", retries=10)
		interactor.typeInputText(self.config["google_account"]["password"])
		interactor.clickOnButtonName("next")
		time.sleep(2)
		interactor.clickOnButtonName("i agree")
		time.sleep(2)
		interactor.clickOnButtonName("widgetswitch0")
		time.sleep(1)
		interactor.clickOnCoordinate(900, 2050) # click on more
		time.sleep(1)
		interactor.clickOnCoordinate(900, 2050) # click on accept
		time.sleep(1)
		interactor.homeButton()

	def readListOfApks(self) -> dict[str, str]:
		filepath = "trafficgen/experiments/randomapp/apklist.csv"
		fullpath = os.path.join(os.getcwd(), filepath)
		finaldict: dict[str, str] = dict()
		if not os.path.isfile(fullpath):
			raise ExperimentFail(f"unable to find list of apk")
		with open(fullpath, 'r') as f:
			for line in f.readlines():
				app_info = line.rstrip().split(";")
				apkname = app_info[0]
				apkpath = app_info[1]
				finaldict[apkname] = apkpath
		logger.info(f"there are {len(self.finaldict)} vpn apps")
		return finaldict

	def installApp(self, app: str) -> None:
		apkdict = self.readListOfApks()
		apkpath = apkdict[app]
		if not os.path.isfile(os.path.join(os.getcwd(), apkpath)):
			raise ExperimentFail(f"unable to find {app} apk")
		self.emulator.installApk(os.path.join(os.getcwd(), apkpath))

	def initializeEmulator(self) -> None:
		# init all the app-controlling objects
		instagram = Instagram(self.emulator)
		self.apps["instagram"] = instagram
		twitter = Twitter(self.emulator)
		self.apps["twitter"] = twitter
		youtube = Youtube(self.emulator)
		self.apps["youtube"] = youtube
		candycrush = CandyCrush(self.emulator)
		self.apps["candycrush"] = candycrush
		spotify = Spotify(self.emulator)
		self.apps["spotify"] = spotify
		discord = Discord(self.emulator)
		self.apps["discord"] = discord
		amazon = Amazon(self.emulator)
		self.apps["amazon"] = amazon
		reddit = Reddit(self.emulator)
		self.apps["reddit"] = reddit

		# if init is specified, start a fresh emulator, wipe data, install apks and do first time setups
		if self.do_init or self.init_only:
			self.emulator.start(wipeData=self.do_init or self.init_only, recordtraffic=False)
			self.emulator.showTapShowPointer()
			self.signIntoGooglePlay()
			self.installApp("youtube")
			self.installApp("twitter")
			# self.installApp("instagram")
			self.installApp("candycrush")
			self.installApp("spotify")
			self.installApp("discord")
			self.installApp("amazon")
			self.installApp("reddit")

			# instagram.openApp(firstOpen=True)
			# self.emulator.interactor.clearUnblockers()
			# self.emulator.interactor.homeButton()
			# self.emulator.interactor.setCurrentApp("")

			twitter.openApp(firstOpen=True)
			self.emulator.interactor.clearUnblockers()
			self.emulator.interactor.homeButton()
			self.emulator.interactor.setCurrentApp("")

			youtube.openApp(firstOpen=True)
			self.emulator.interactor.clearUnblockers()
			self.emulator.interactor.homeButton()
			self.emulator.interactor.setCurrentApp("")

			candycrush.openApp(firstOpen=True)
			self.emulator.interactor.clearUnblockers()
			self.emulator.interactor.homeButton()
			self.emulator.interactor.setCurrentApp("")

			spotify.openApp(firstOpen=True)
			self.emulator.interactor.clearUnblockers()
			self.emulator.interactor.homeButton()
			self.emulator.interactor.setCurrentApp("")

			discord.openApp(firstOpen=True)
			self.emulator.interactor.clearUnblockers()
			self.emulator.interactor.homeButton()
			self.emulator.interactor.setCurrentApp("")

			amazon.openApp(firstOpen=True)
			self.emulator.interactor.clearUnblockers()
			self.emulator.interactor.homeButton()
			self.emulator.interactor.setCurrentApp("")

			reddit.openApp(firstOpen=True)
			self.emulator.interactor.clearUnblockers()
			self.emulator.interactor.homeButton()
			self.emulator.interactor.setCurrentApp("")

			# if only do init, we are pretty much done here
			if self.init_only:
				return
			# stop emulator and start it again for real testing
			self.emulator.stop()
			time.sleep(10)

		self.emulator.start(wipeData=False, recordtraffic=True)
		self.emulator.showTapShowPointer()
		time.sleep(2)

		# for some very annoying reasons, instagram does not behave and require us to re-initialize it everytime emulator restarts
		self.emulator.uninstallApp("com.instagram.android")
		self.installApp("instagram")
		instagram.openApp(firstOpen=True)
		self.emulator.interactor.clearUnblockers()
		self.emulator.interactor.homeButton()
		self.emulator.interactor.setCurrentApp("")
		time.sleep(2)

	def getNextMilestone(self) -> float:
		# low: 1-3 apps per 10 minutes
		noFasterThan = 180.0
		noSlowerThan = 650.0
		# medium: 4-5 apps per 10 minutes
		if self.config["randomapp"]["app_frequency_profile"] == "medium":
			noFasterThan = 110.0
			noSlowerThan = 220.0
		# high: 7-9 apps per 10 minutes
		if self.config["randomapp"]["app_frequency_profile"] == "high":
			noFasterThan = 50.0
			noSlowerThan = 110.0
		return random.uniform(noFasterThan, noSlowerThan)

	def runExperiment(self):
		try:
			# initialize
			self.initializeEmulator()
			if self.init_only:
				return
			timeLimit = utils.randomizeTimeLimit(self.config["time_limit"] * 60) # in seconds
			stuckCounter = 0
			startTime = time.time()
			timeLeft = timeLimit # in seconds
			events = [self.emulator.interactor.timeoutEvent]
			for _, app in self.apps.items():
				events.append(app.timeoutEvent)

			# start the main loop
			while True:

				# choose a random app
				appChoiceKey = random.choice(list(self.apps.keys()))
				appChoice = self.apps[appChoiceKey]

				# calculate time left and set timers
				currentTime = time.time()
				elapsedTime = currentTime - startTime
				timeLeft -= elapsedTime
				if timeLeft <= 0:
					break
				nextMilestoneDuration = self.getNextMilestone()
				timer_thread = threading.Thread(target=utils.eventsTimer, args=(events, nextMilestoneDuration))
				timer_thread.start()
				startTime = time.time()

				try:
					# open app
					appChoice.openApp()
					if self.visitedApps.get(appChoiceKey, {}):
						appChoice.goHome()
					self.visitedApps[appChoiceKey] = True

					try:
						while True:
							try:
								appChoice.interact()
								break
							except ExecUnstucked as e:
								logger.info("recovered from a stuck scenario")
								stuckCounter += 1
								if stuckCounter >= 7:
									logger.info("stuck 7 times.")
									raise ExecStuck("unstuck too many times")
								if stuckCounter >= 5:
									logger.info("stuck 5 times.")
									self.emulator.interactor.homeButton()
									self.emulator.openApp(self.emulator.interactor.currentApp)
									self.emulator.interactor.closeApp()
					except ExecTimeout as e:
						logger.info("time to switch app")
				except ExecUnstucked as e:
					logger.info("recovered from a stuck scenario")
					logger.info("trying a different app")
					for event in events:
						event.set()
				except ExecStuck as e:
					logger.info("stuck too many times, switching app")
					for event in events:
						event.set()

				timer_thread.join()
				# clear the events
				for event in events:
					event.clear()
				self.emulator.interactor.homeButton()
				self.emulator.interactor.setCurrentApp("")
				self.emulator.interactor.clearUnblockers()
				stuckCounter = 0

			logger.info("experiment completed!")

		except Exception as e:
			logger.error(f"the experiment has been interrupted by an error: {e}")
			traceback.print_exc()

			if self.config["emulator"]["keep_on_after_failure"]:
				logger.info("leaving the emulator running for debugging purposes ...")
				while True:
					time.sleep(100)
