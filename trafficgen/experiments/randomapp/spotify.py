
import random
import time
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi

import logging

from trafficgen.interactor import InteractionAction
logger = logging.getLogger(__name__)

class Spotify(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)
		self.mode: str = "home"

	def cardCenterIsClickable(self, action: InteractionAction) -> bool:
		xcenter = (float(action.x) + float(action.xxe)) / 2.0
		ycenter = (float(action.y) + float(action.yye)) / 2.0
		return ycenter > 300 and ycenter < 2000 and xcenter > 0 and xcenter < 1077

	def listenToMusicForSomeTime(self) -> None:
		noShorterThan = 80
		noLongerThan = 145
		if self.emulator.activity_profile == "medium":
			noShorterThan = 40
			noLongerThan = 110
		if self.emulator.activity_profile == "high":
			noShorterThan = 20
			noLongerThan = 70
		self.emulator.interactor.waitRandom(noShorterThan=noShorterThan, noLongerThan=noLongerThan)

	def clickOnRandomCardAndPlay(self):
		# assuming at spotify home screen
		# choose a random card
		actions = self.emulator.interactor.getActions()
		clickableCards = {key: value for key, value in actions.items() if value.resid=="com.spotify.music:id/card_root" and self.cardCenterIsClickable(value)}
		if not clickableCards:
			raise ErrNoAction("no clickable cards in view")
		randomKey = random.choice(list(clickableCards.keys()))
		logger.info(f"clicking on a random spotify card {randomKey}")
		actions[randomKey].touch()
		time.sleep(2)
		# do we see a play button?
		actions = self.emulator.interactor.getActions()
		if "play artist" not in actions and "play playlist" not in actions:
			logger.info("nothing to play, pressing back button")
			self.emulator.interactor.backButton()
			return
		# random chance of toggle shuffle
		toggleChoice = random.choice([True, False])
		if toggleChoice:
			if "enable shuffle for this playlist" in actions:
				actions["enable shuffle for this playlist"].touch()
			elif "disable shuffle for this playlist" in actions:
				actions["disable shuffle for this playlist"].touch()
			elif "enable shuffle for this artist" in actions:
				actions["enable shuffle for this artist"].touch()
			elif "disable shuffle for this artist" in actions:
				actions["disable shuffle for this artist"].touch()
		# now press play button
		if "play artist" in actions:
			actions["play artist"].touch()
		if "play playlist" in actions:
			actions["play playlist"].touch()
		# idle for a while then go back
		self.listenToMusicForSomeTime()
		self.emulator.interactor.backButton()

	def addCurrentSongToLikedSongs(self):
		actions = self.emulator.interactor.getActions()
		if "add item" in actions:
			logger.info("adding current song to liked")
			actions["add item"].touch()

	def openSearchMenu(self):
		# open search
		logger.info("opening search menu")
		self.emulator.interactor.clickOnCoordinate(400, 2050)
		self.emulator.interactor.scrollDownShortFlick()
		self.mode = "search"

	def clickOnRandomCardAndPlaySearchMode(self):
		# assuming at search menu
		# choose a random genre
		actions = self.emulator.interactor.getActions()
		clickableCards = {key: value for key, value in actions.items() if value.resid=="com.spotify.music:id/card" and self.cardCenterIsClickable(value)}
		if not clickableCards:
			raise ErrNoAction("no clickable cards in view")
		randomKey = random.choice(list(clickableCards.keys()))
		logger.info(f"clicking on a random spotify card {randomKey}")
		actions[randomKey].touch()
		time.sleep(2)
		# choose a random card
		actions = self.emulator.interactor.getActions()
		clickableCards = {key: value for key, value in actions.items() if key.endswith("followers")and self.cardCenterIsClickable(value)}
		if not clickableCards:
			raise ErrNoAction("no clickable cards in view")
		randomKey = random.choice(list(clickableCards.keys()))
		logger.info(f"clicking on a random spotify card {randomKey}")
		actions[randomKey].touch()
		time.sleep(2)
		# do we see a play button?
		actions = self.emulator.interactor.getActions()
		if "play artist" not in actions and "play playlist" not in actions:
			logger.info("nothing to play, pressing back button")
			self.emulator.interactor.backButton()
			return
		# random chance of toggle shuffle
		toggleChoice = random.choice([True, False])
		if toggleChoice:
			logger.info("toggling shuffle")
			if "enable shuffle for this playlist" in actions:
				actions["enable shuffle for this playlist"].touch()
			elif "disable shuffle for this playlist" in actions:
				actions["disable shuffle for this playlist"].touch()
			elif "enable shuffle for this artist" in actions:
				actions["enable shuffle for this artist"].touch()
			elif "disable shuffle for this artist" in actions:
				actions["disable shuffle for this artist"].touch()
		# now press play button
		if "play artist" in actions:
			actions["play artist"].touch()
		if "play playlist" in actions:
			actions["play playlist"].touch()
		# idle for a while then go back
		self.listenToMusicForSomeTime()
		self.emulator.interactor.backButton()

	def togglePlayPause(self) -> None:
		actions = self.emulator.interactor.getActions()
		if "pause" in actions:
			actions["pause"].touch()
		if "play" in actions:
			actions["play"].touch()

	def goHome(self) -> None:
		logger.info("trying to return to spotify home screen...")
		self.emulator.interactor.clickOnCoordinate(135, 2060)
		self.mode = "home"
		time.sleep(2)

	def openApp(self, firstOpen=False) -> None:
		self.emulator.openApp("com.spotify.music")
		self.emulator.interactor.setCurrentApp("com.spotify.music")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		time.sleep(5)
		if firstOpen:
			logger.info("spotify first open, doing logins and setups")
			self.emulator.interactor.clickOnButtonName("continue with google")
			time.sleep(7)

	def interact(self) -> None:
		while True:
			try:
				choiceOptions: list[callable] = []
				choiceWeights: list[int] = []
				choiceOptions.append(self.emulator.interactor.randomScrollDown)
				choiceWeights.append(10)
				choiceOptions.append(self.addCurrentSongToLikedSongs)
				choiceWeights.append(5)
				choiceOptions.append(self.togglePlayPause)
				choiceWeights.append(3)
				if self.mode == "home":
					choiceOptions.append(self.clickOnRandomCardAndPlay)
					choiceWeights.append(7)
					choiceOptions.append(self.openSearchMenu)
					choiceWeights.append(5)
				if self.mode == "search":
					choiceOptions.append(self.clickOnRandomCardAndPlaySearchMode)
					choiceWeights.append(7)
					choiceOptions.append(self.goHome)
					choiceWeights.append(15)
				option = random.choices(population=choiceOptions,weights=choiceWeights)
				option[0]()
				if option[0] != self.clickOnRandomCardAndPlay and option[0] != self.clickOnRandomCardAndPlaySearchMode:
					self.emulator.interactor.waitRandom()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")
