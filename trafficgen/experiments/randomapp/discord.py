
import random
import time
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi

import logging
logger = logging.getLogger(__name__)

class Discord(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)

	def goHome(self) -> None:
		logger.info("trying to return to discord home screen...")
		for i in range(5):
			actions = self.emulator.interactor.getActions()
			if "add friends" and "new message" in actions:
				self.emulator.interactor.clickOnCoordinate(140, 2060)
				# click on servers button
			if "add a server" and "search" and "invite" in actions:
				break
			self.emulator.interactor.backButton()
			time.sleep(3)

	def openApp(self, firstOpen=False) -> None:
		self.emulator.openApp("com.discord")
		self.emulator.interactor.setCurrentApp("com.discord")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		time.sleep(8)
		if firstOpen:
			logger.info("discord first open, doing logins and setups")
			self.emulator.interactor.clickOnCoordinate(550, 2045) # log in button
			time.sleep(1)
			self.emulator.interactor.clickOnButtonName("textfield0")
			self.emulator.interactor.typeInputText(self.emulator.config["google_account"]["email"])
			time.sleep(1)
			self.emulator.interactor.clickOnButtonName("textfield1")
			self.emulator.interactor.typeInputText(self.emulator.config["discord_account"]["password"])
			time.sleep(1)
			self.emulator.interactor.clickOnButtonName("log in")
			time.sleep(5)
		self.goHome()

	def sendAMessage(self):
		chosenMessage = random.choice([
			"Hey there! Hows your day going?",
			"Good morning! Any exciting plans for the day?",
			"Hi! Did you catch the latest episode of [popular TV show]?",
			"Hello! Just checking in. How are you feeling today?",
			"Hey! Have you tried that new restaurant in town?",
			"Hi! Whats the best book youve read recently?",
			"Hello! Any recommendations for a good movie to watch?",
			"Hey there! How was your weekend?",
			"Hi! Are you a coffee or tea person?",
			"Hello! Whats your favorite way to relax after a long day?",
		])
		logger.info("sending a message")
		self.emulator.interactor.clickOnButtonName("spammable (text channel)")
		self.emulator.interactor.waitRandom()
		self.emulator.interactor.clickOnCoordinate(600, 2070) # open chat text input
		time.sleep(1)
		self.emulator.interactor.typeInputText(chosenMessage)
		time.sleep(1)
		self.emulator.interactor.clickOnButtonName("send")
		self.emulator.interactor.waitRandom()
		self.emulator.interactor.backButton()
		self.emulator.interactor.backButton()

	def sendASticker(self):
		logger.info("sending a sticker")
		self.emulator.interactor.clickOnButtonName("spammable (text channel)")
		time.sleep(1)
		self.emulator.interactor.clickOnCoordinate(850, 2070) # open emoji menu
		time.sleep(1)
		self.emulator.interactor.clickOnCoordinate(878, 1576) # change to sticker mode
		self.emulator.interactor.waitRandom()
		self.emulator.interactor.scroll(520, 1900, 520, 600, duration=120) # expand the sticker drawer
		for i in range(2):
			scrollOrNot = random.choice([True, False])
			if scrollOrNot:
				self.emulator.interactor.randomScrollDown()
			time.sleep(3)
		self.emulator.interactor.clickOnRandomButtonName("android.widget.framelayout")
		self.emulator.interactor.waitRandom()
		self.emulator.interactor.backButton()
		self.emulator.interactor.backButton()

	def watchAVideo(self):
		logger.info("watching a video")
		self.emulator.interactor.clickOnButtonName("watchable (text channel)")
		time.sleep(1)
		scrollOrNot = random.choice([True, False])
		if scrollOrNot:
			self.emulator.interactor.scrollUpHalfPage()
		time.sleep(1)
		self.emulator.interactor.clickOnRandomButtonName("play full video")
		self.emulator.interactor.waitRandom()
		self.emulator.interactor.backButton()

	def interact(self) -> None:
		while True:
			try:
				option = random.choices([
					self.sendAMessage,
					self.sendASticker,
					self.watchAVideo,
				], weights=[10, 10, 10])
				option[0]()
				self.emulator.interactor.waitRandom()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")
		pass
