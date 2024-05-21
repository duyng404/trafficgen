

import os
import random
import time
import xml.dom.minidom as xx
from trafficgen import utils
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction, ExecStuck
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi

import logging
logger = logging.getLogger(__name__)

class Twitter(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)

	def isLoginScreen(self) -> bool:
		actions = self.emulator.interactor.getActions()
		if "create account" in actions:
			return True
		return False

	def isLoginScreenWithGoogle(self) -> bool:
		actions = self.emulator.interactor.getActions()
		if "create account" in actions and "continue with google" in actions:
			return True
		return False

	def getConfirmRepostButton(self, dumpf) -> dict:
		logger.debug("Analyzing UI for actions ...")
		if not dumpf:
			return {}
		if not os.path.isfile(dumpf):
			logger.error("Failed to obtain UI dump for APK. Exiting UI interaction")
			return {}
		dump = xx.parse(dumpf)
		if not dump:
			logger.error("Cannot parse dumped UI for some reason")
			return {}
		nodes = dump.getElementsByTagName("node")
		for elem in nodes:
			actionname: str = elem.getAttribute("text").lower()
			if actionname != "repost" and actionname != "undo repost":
				continue
			coordinates = elem.getAttribute("bounds")
			coordinates = self.emulator.interactor.get_coordinates(coordinates)
			if len(actionname) >= 1:
				return {"xy": coordinates}
		return {}

	@utils.timeoutChecker()
	def clickOnRandomLike(self) -> None:
		self.emulator.interactor.clickOnRandomButtonName("com.twitter.android:id/inline_like")
		time.sleep(2)

	@utils.timeoutChecker()
	def clickOnRandomRetweet(self) -> None:
		# click on a retweet button
		self.emulator.interactor.clickOnRandomButtonName("com.twitter.android:id/inline_retweet")
		# confirm retweet OR undo retweet
		dumpf = self.emulator.interactor.get_uidump()
		actions = self.getConfirmRepostButton(dumpf)
		if not actions:
			raise ErrNoAction("cannot find confirm retweet button")
		logger.info("clicking on confirm retweet button")
		x, y, xxe, yye = actions["xy"]
		self.emulator.interactor.clickOnCoordinate(x, y, xxe, yye)
		time.sleep(2)

	@utils.timeoutChecker()
	def clickOnBackButton(self) -> None:
		self.emulator.interactor.clickOnCoordinate(80, 240)

	@utils.timeoutChecker()
	def visitRandomProfile(self) -> None:
		logger.info("visiting a random profile")
		# click on a profile picture
		self.emulator.interactor.clickOnRandomButtonName("profile image")
		# scroll for a bit
		time.sleep(3)
		self.interactScrollLikeRetweet()
		# press back button
		self.clickOnBackButton()
		time.sleep(2)

	@utils.timeoutChecker()
	def viewRandomImage(self) -> None:
		logger.info("viewing a random image")
		# click on a random image
		self.emulator.interactor.clickOnRandomButtonName("image")
		# wait for a bit
		self.emulator.interactor.waitRandom()
		# back
		self.clickOnBackButton()
		time.sleep(2)

	@utils.timeoutChecker()
	def viewRandomPost(self) -> None:
		logger.info("visiting a random post")
		# click on a post
		actions = self.emulator.interactor.getActions()
		clickableProfilePics = {key: value for key, value in actions.items() if key.startswith("profile image")}
		if not clickableProfilePics:
			raise ErrNoAction("no clickable profile pics in view")
		randomKey = random.choice(list(clickableProfilePics.keys()))
		logger.info(f"clicking on profile {randomKey}")
		actions[randomKey].touch()
		# scroll for a bit
		time.sleep(1)
		self.emulator.interactor.scrollSeveralTimes()
		# press back button
		self.clickOnBackButton()
		time.sleep(1)

	def interactScrollLikeRetweet(self) -> None:
		repeats = random.randint(1,2)
		for i in range(repeats):
			option = random.choices([
				self.emulator.interactor.randomScrollDown,
				self.clickOnRandomLike,
				self.clickOnRandomRetweet,
			], weights=[10, 1, 1])
			option[0]()
			self.emulator.interactor.waitRandom()

	def goHome(self) -> None:
		logger.info("trying to return to twitter home screen...")
		for i in range(20):
			actions = self.emulator.interactor.getActions(stuckFactor=0)
			if "search" in actions and "apps list" in actions:
				break
			self.emulator.interactor.backButton()
		else:
			raise ExecStuck("cant return to twitter homescreen")
		self.emulator.openApp("com.twitter.android")

	def openApp(self, firstOpen=False) -> None:
		self.emulator.openApp("com.twitter.android")
		self.emulator.interactor.setCurrentApp("com.twitter.android")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		time.sleep(5)
		if firstOpen:
			logger.info("twitter first open, doing setups and logins")
			if self.isLoginScreen():
				for i in range(10):
					if self.isLoginScreenWithGoogle():
						self.emulator.interactor.clickOnButtonName("continue with google")
						time.sleep(10)
						break
					else:
						self.emulator.interactor.closeApp()
						self.emulator.openApp("com.twitter.android")
						time.sleep(5)
		else:
			time.sleep(5)
		self.emulator.interactor.clickOnCoordinate(110, 2070) # click on Home

	def interact(self) -> None:
		while True:
			try:
				option = random.choices([
					self.emulator.interactor.scrollSeveralTimes,
					self.clickOnRandomLike,
					self.clickOnRandomRetweet,
					self.viewRandomPost,
					self.viewRandomImage,
					self.visitRandomProfile,
				], weights=[10, 3, 1, 5, 6, 3])
				option[0]()
				self.emulator.interactor.waitRandom()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")

