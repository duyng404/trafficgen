


import random
import time
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction, ExecStuck
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi

import logging
logger = logging.getLogger(__name__)

class Reddit(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)
		self.currentView = "home"

	def goHome(self) -> None:
		logger.info("trying to return to reddit home screen...")
		for i in range(20):
			actions = self.emulator.interactor.getActions()
			if "feed_switcher_button" in actions:
				break
			self.emulator.interactor.backButton()
			time.sleep(2)
		else:
			raise ExecStuck("cant go back to reddit home screen")
		self.emulator.interactor.clickOnCoordinate(120, 2060) # click on home
		self.currentView = "home"
		time.sleep(3)

	def openApp(self, firstOpen=False) -> None:
		self.emulator.openApp("com.reddit.frontpage")
		self.emulator.interactor.setCurrentApp("com.reddit.frontpage")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		time.sleep(5)
		if firstOpen:
			logger.info("reddit first open, doing logins and setups")
			self.emulator.interactor.clickOnButtonName("continue with google")
			time.sleep(10)

	def upvoteFrontpage(self):
		self.emulator.interactor.clickOnRandomButtonName("post_vote_section")

	def upvotePostView(self):
		self.emulator.interactor.clickOnRandomButtonName("upvote")

	def clickOnRandomPost(self):
		self.emulator.interactor.clickOnRandomButtonName("post_unit")
		self.currentView = "post"

	def returnFromPost(self):
		self.emulator.interactor.backButton()
		self.currentView = "home"

	def interact(self) -> None:
		while True:
			try:
				choiceOptions: list[callable] = []
				choiceWeights: list[int] = []
				choiceOptions.append(self.emulator.interactor.randomScrollDown)
				choiceWeights.append(10)
				if self.currentView == "home":
					choiceOptions.append(self.upvoteFrontpage)
					choiceWeights.append(4)
					choiceOptions.append(self.clickOnRandomPost)
					choiceWeights.append(5)
				if self.currentView == "post":
					choiceOptions.append(self.upvotePostView)
					choiceWeights.append(2)
					choiceOptions.append(self.returnFromPost)
					choiceWeights.append(10)
				option = random.choices(population=choiceOptions,weights=choiceWeights)
				option[0]()
				self.emulator.interactor.waitRandom()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")
		pass
