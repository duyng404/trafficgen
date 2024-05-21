


import random
import time
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi

import logging
logger = logging.getLogger(__name__)

class Youtube(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)
		self.viewingVideo = False

	def clickOnRandomVideo(self) -> None:
		actions = self.emulator.interactor.getActions()
		clickableVideos = {key: value for key, value in actions.items() if key.endswith("play video") and not key.startswith("ad")}
		if not clickableVideos:
			raise ErrNoAction("no clickable video in view")
		randomKey = random.choice(list(clickableVideos.keys()))
		logger.info(f"clicking on new video {randomKey}")
		actions[randomKey].touch()
		time.sleep(2)
		self.watchVideoForSomeTime()

	def watchVideoForSomeTime(self) -> None:
		noShorterThan = 30
		noLongerThan = 120
		if self.emulator.activity_profile == "medium":
			noShorterThan = 15
			noLongerThan = 60
		if self.emulator.activity_profile == "high":
			noShorterThan = 5
			noLongerThan = 30
		self.emulator.interactor.waitRandom(noShorterThan=noShorterThan, noLongerThan=noLongerThan)

	def goHome(self) -> None:
		logger.info("trying to return to youtube home screen...")
		while True:
			actions = self.emulator.interactor.getActions(stuckFactor=0)
			if "notifications" not in actions and "search" not in actions:
				self.emulator.interactor.backButton()
				time.sleep(1)
				continue
			break
		self.emulator.interactor.clickOnCoordinate(110, 2070)
		time.sleep(1)
		self.emulator.interactor.scrollUpHalfPage()
		time.sleep(1)
		self.emulator.interactor.scrollUpHalfPage()
		time.sleep(5)

	def openApp(self, firstOpen=False) -> None:
		self.emulator.openApp("com.google.android.youtube")
		self.emulator.interactor.setCurrentApp("com.google.android.youtube")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		time.sleep(5)
		if firstOpen:
			logger.info("youtube first open, doing logins and setups")
			self.emulator.interactor.closeApp()
			self.emulator.openApp("com.google.android.youtube")
			time.sleep(5)

	def interact(self) -> None:
		while True:
			try:
				option = random.choices([
					self.emulator.interactor.randomScrollDown,
					self.clickOnRandomVideo,
				], weights=[10, 5])
				option[0]()
				if option[0] != self.clickOnRandomVideo:
					self.emulator.interactor.waitRandom()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")
