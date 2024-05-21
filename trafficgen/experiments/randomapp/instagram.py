
import random
import time
from trafficgen import utils
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi

import logging

from trafficgen.interactor import InteractionAction
logger = logging.getLogger(__name__)

class Instagram(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)
		self.currentMode = "posts"

	def isLoginScreen(self) -> dict[str, InteractionAction]:
		actions = self.emulator.interactor.getActions(stuckFactor=0)
		if "log in" in actions and "forgot password?" in actions:
			return actions
		return {}

	def isPartialLoginScreen(self) -> dict[str, InteractionAction]:
		actions = self.emulator.interactor.getActions(stuckFactor=0)
		if "log in" in actions and "log into another account" in actions:
			return actions
		return {}

	@utils.timeoutChecker()
	def clickOnRandomLike(self) -> None:
		self.emulator.interactor.clickOnRandomButtonName("like")

	@utils.timeoutChecker()
	def openRandomCommentSection(self) -> None:
		self.emulator.interactor.clickOnRandomButtonName("comment")
		time.sleep(1)
		self.emulator.interactor.backButton()
		# wait a bit
		self.emulator.interactor.waitRandom()
		# back
		self.emulator.interactor.backButton()

	@utils.timeoutChecker()
	def clickOnRandomFollow(self) -> None:
		self.emulator.interactor.clickOnRandomButtonName("follow")

	def waitForHomePage(self) -> None:
		logger.info("making sure we are at instagram home screen...")
		for i in range(20):
			actions = self.emulator.interactor.getActions()
			if "instagram home feed" or "no unread messages" in actions:
				return
			time.sleep(2)

	def switchMode(self) -> None:
		logger.info("switching instagram mode (posts/reels)")
		if self.currentMode == "posts":
			self.emulator.interactor.clickOnCoordinate(750, 2080) # switch to reels
			self.currentMode = "reels"
		if self.currentMode == "reels":
			self.emulator.interactor.clickOnCoordinate(110, 2070) # click on Home
			self.currentMode = "posts"
		self.emulator.interactor.waitRandom()

	def goHome(self) -> None:
		logger.info("trying to go back to instagram home screen")
		self.emulator.interactor.clickOnCoordinate(110, 2070) # click on Home
		time.sleep(1)
		self.emulator.interactor.scrollUpHalfPage()
		time.sleep(5)

	def openApp(self, firstOpen = False) -> None:
		self.emulator.openApp("com.instagram.android")
		self.emulator.interactor.setCurrentApp("com.instagram.android")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		if firstOpen:
			logger.info("instagram first open, setting up & logging in")
			time.sleep(10)
			for i in range(10):
				actions = self.isPartialLoginScreen()
				if actions:
					# self.emulator.interactor.vcclickOnElementName("log in")
					# self.emulator.interactor.clickOnButtonName("log into another account")
					actions["log in"].touch()
					time.sleep(5)
					break
				actions2 = self.isLoginScreen()
				if actions2:
					self.emulator.interactor.clickOnButtonName("textfield0")
					time.sleep(1)
					self.emulator.interactor.typeInputText(self.emulator.config["google_account"]["email"])
					self.emulator.interactor.clickOnButtonName("textfield1")
					time.sleep(1)
					self.emulator.interactor.typeInputText(self.emulator.config["instagram_account"]["password"])
					self.emulator.interactor.clickOnButtonName("log in")
					break
				time.sleep(2)
		time.sleep(5)
		self.waitForHomePage()
		self.emulator.interactor.clickOnCoordinate(110, 2070) # click on Home

	def interact(self) -> None:
		while True:
			try:
				option = random.choices([
					self.emulator.interactor.randomScrollDown,
					self.clickOnRandomFollow,
					self.clickOnRandomLike,
					self.openRandomCommentSection,
				], weights=[10, 1, 3, 4])
				option[0]()
				self.emulator.interactor.waitRandom()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")
