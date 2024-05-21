
import os
import random
import threading
import time
import traceback
from trafficgen import utils
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction, ExecUnstucked, ExecTimeout, ExperimentFail, ShellExecFail
from trafficgen.experiments.randombrowse.unblocker import POPUP_KEYWORDS, checkForBlockingUi
from trafficgen.interactor import InteractionAction

import logging
logger = logging.getLogger(__name__)

class Domain:
	def __init__(self, domain: str, needsLogin: bool, isSearchEngine: bool, isStreamingSvc: bool):
		self.domain = domain
		self.needsLogin = needsLogin
		self.isSearchEngine = isSearchEngine
		self.isStreamingSvc = isStreamingSvc
		self.visited: bool = False

class ExperimentRunner:
	def __init__(self, emulator:AndroidEmulator, do_init: bool, existing_emulator: bool):
		self.emulator = emulator
		self.do_init = do_init
		self.existing_emulator = existing_emulator
		self.config = emulator.config
		self.domains: list[Domain] = []
		self.searchKeywords: list[str] = []
		self.siteState: dict = {} # temporary dict to store state of current site being browsed

	def openChrome(self, firstTime=False) -> None:
		interactor = self.emulator.interactor
		self.emulator.openApp("com.android.chrome")
		time.sleep(1)
		if firstTime:
			interactor.clickOnButtonName("help make chrome better by sending usage statistics and crash reports to google.")
			time.sleep(1)
			interactor.clickOnCoordinate(540, 2055) # click on accept & continue
			time.sleep(1)
			interactor.clickOnButtonName("no thanks")
			time.sleep(2)

	def checkRunningEmulator(self) -> bool:
		def callback(result):
			if str(result.stdout).rstrip() == "1":
				return True
			else:
				return False
		try:
			isRunning = utils.executeShell("adb shell getprop sys.boot_completed", callbackSuccess=callback, captureOutput=True)
			return isRunning
		except ShellExecFail:
			return False

	def initializeEmulator(self) -> None:
		if not self.existing_emulator:
			if self.do_init:
				logger.info("performing first time open google chrome")
				self.emulator.start(wipeData=True, recordtraffic=True)
				self.openChrome(firstTime=True)
				self.emulator.interactor.homeButton()
				time.sleep(5)
			else:
				self.emulator.start(wipeData=False, recordtraffic=True)
		self.emulator.showTapShowPointer()
		# clear chrome tabs
		logger.info("clearing all chrome tabs")
		self.openChrome()
		actions = self.emulator.interactor.getActions(stuckFactor=0)
		for action in actions:
			if "tap to switch tabs" in action:
				actions[action].touch()
				break
		self.emulator.interactor.clickOnButtonName("more options")
		self.emulator.interactor.clickOnButtonName("android.widget.linearlayout1") # click on close all tabs
		time.sleep(1)
		self.emulator.interactor.homeButton()
		time.sleep(2)

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

	def readListOfDomains(self):
		filepath = "trafficgen/experiments/randombrowse/alexa_list.txt"
		fullpath = os.path.join(os.getcwd(), filepath)
		if not os.path.isfile(fullpath):
			raise ExperimentFail(f"unable to find list of domains")
		with open(fullpath, 'r') as f:
			for line in f.readlines():
				domain_info = line.rstrip().split(" ")
				if domain_info[0] == "domain":
					continue # skip first line in file
				self.domains.append(Domain(
					domain=domain_info[0],
					needsLogin=domain_info[1]=="yes",
					isSearchEngine=domain_info[2]=="yes",
					isStreamingSvc=domain_info[3]=="yes",
				))

	def readListOfSearchKeywords(self):
		filepath = "trafficgen/experiments/randombrowse/search_keywords.txt"
		fullpath = os.path.join(os.getcwd(), filepath)
		if not os.path.isfile(fullpath):
			raise ExperimentFail(f"unable to find list of domains")
		with open(fullpath, 'r') as file:
			self.searchKeywords = [line.strip() for line in file]

	def getARandomDomain(self) -> Domain:
		while True:
			choice = random.choice(self.domains)
			if not choice.visited:
				return choice

	def isCenterClickable(self, action: InteractionAction) -> bool:
		xcenter = (float(action.x) + float(action.xxe)) / 2.0
		ycenter = (float(action.y) + float(action.yye)) / 2.0
		return ycenter > 300 and ycenter < 2000 and xcenter > 0 and xcenter < 1077

	def checkForPrioritizedActions(self, domain:Domain) -> tuple[dict[str, InteractionAction], list[callable, int]]:
		rawActions = self.emulator.interactor.getActions(stuckFactor=1)
		actions = {key: value for key, value in rawActions.items() if self.isCenterClickable(value)}
		if POPUP_KEYWORDS.get(domain.domain, []):
			popupActions = {key: value for key, value in actions.items() if key in POPUP_KEYWORDS[domain.domain]}
		else:
			popupActions = {key: value for key, value in actions.items() if key in POPUP_KEYWORDS["*"]}
		if len(popupActions) > 0:
			return rawActions, [(value.touch, 10) for key, value in popupActions.items()]
		if domain.isSearchEngine:
			if self.siteState.get("searchPerformed", False):
				return rawActions, []
			# click on textfield
			self.emulator.interactor.clickOnButtonName("textfield0")
			# enter text
			time.sleep(1)
			keyword = random.choice(self.searchKeywords)
			logger.info(f"keyword={keyword}")
			self.emulator.interactor.typeInputText(keyword)
			time.sleep(1)
			# perform search
			self.emulator.interactor.enterKey()
			self.siteState["searchPerformed"] = True
			# scroll (maybe)
			scrollOrNot = random.choice([True, False])
			if scrollOrNot:
				self.emulator.interactor.scrollDownHalfPage()
			# wait a bit
			self.emulator.interactor.waitRandom()
			return rawActions, []
		if domain.domain == "youtube.com":
			self.emulator.interactor.scrollUpHalfPage()
			self.emulator.interactor.waitRandom()
			return rawActions, []
		else:
			return rawActions, [] # catch-all

	def sanitizeActions(self, actions:dict[str, InteractionAction]) -> dict[str, InteractionAction]:
		if not actions:
			actions = self.emulator.interactor.getActions(stuckFactor=1)
		# in range to click
		actions = {key: value for key, value in actions.items() if self.isCenterClickable(value)}
		# remove ads
		actions = {key: value for key, value in actions.items() if "ad" not in key and "sponsored" not in key}
		return actions

	def clickOnSomething(self, actions:dict[str, InteractionAction] = {}) -> None:
		actions = self.sanitizeActions(actions)
		if not actions:
			raise ErrNoAction("no clickable actions in view")
		randomKey = random.choice(list(actions.keys()))
		logger.info(f"clicking on a random button {randomKey}")
		actions[randomKey].touch()

	def performBrowsing(self, domain: Domain) -> None:
		utils.executeShell(f"adb shell am start -n com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity -d 'https://{domain.domain}/'")
		self.emulator.interactor.setCurrentApp("com.android.chrome", "org.chromium.chrome.browser.ChromeTabbedActivity", f"https://{domain.domain}/")
		self.emulator.interactor.waitRandom()
		clicksSoFar: int = 0
		while True:
			try:
				# check if there is any special actions for this specific website
				actions, choices = self.checkForPrioritizedActions(domain)
				if not choices:
					choices = [
						(self.emulator.interactor.randomScrollDown, 10),
						(self.clickOnSomething, 6),
					]
					if clicksSoFar > 0:
						choices.append(
							(self.emulator.interactor.backButton, 6)
						)
				option = random.choices(
					population=[choice[0] for choice in choices],
					weights=[choice[1] for choice in choices],
				)
				if option[0] == self.clickOnSomething:
					self.emulator.interactor.saveDump()
					self.clickOnSomething(actions)
					if self.emulator.interactor.compareDump():
						clicksSoFar += 1
				else:
					option[0]()
				self.emulator.interactor.waitRandom()
				if option[0] == self.emulator.interactor.backButton:
					clicksSoFar -= 1
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")

	def runExperiment(self):
		try:
			# inits
			self.readListOfDomains()
			self.readListOfSearchKeywords()
			if self.existing_emulator:
				running = self.checkRunningEmulator()
				if not running:
					logger.error("no running emulator found :D ?")
					return
			self.initializeEmulator()
			self.emulator.interactor.addUnblocker(checkForBlockingUi)
			timeLimit = utils.randomizeTimeLimit(self.config["time_limit"] * 60) # in seconds
			startTime = time.time()
			timeLeft = timeLimit # in seconds
			events = [self.emulator.interactor.timeoutEvent]

			# start the main loop
			while True:

				# choose a random domain
				domain = self.getARandomDomain()
				if domain.needsLogin:
					logger.info(f"skipping {domain.domain} because logging in to social media is not implemented.")
					domain.visited = True
					continue

				# calculate time left and set timers
				currentTime = time.time()
				elapsedTime = currentTime - startTime
				timeLeft -= elapsedTime
				if timeLeft <= 0:
					break
				nextMilestoneDuration = self.getNextMilestone()
				logger.info(f"next switch milestone is in {nextMilestoneDuration}")
				timer_thread = threading.Thread(target=utils.eventsTimer, args=(events, nextMilestoneDuration))
				timer_thread.start()
				startTime = time.time()

				# do the browsing
				try:
					while True:
						try:
							self.performBrowsing(domain)
							break
						except ExecUnstucked as e:
							logger.info("recovered from a stuck scenario")
				except ExecTimeout as e:
					logger.info("time to switch app")

				domain.visited = True
				self.siteState.clear()
				timer_thread.join()
				self.emulator.interactor.setCurrentApp("")
				# clear the events
				for event in events:
					event.clear()
				self.emulator.interactor.homeButton()


		except Exception as e:
			logger.error(f"the experiment has been interrupted by an error: {e}")
			traceback.print_exc()

			if self.config["emulator"]["keep_on_after_failure"]:
				logger.info("leaving the emulator running for debugging purposes ...")
				while True:
					time.sleep(100)
