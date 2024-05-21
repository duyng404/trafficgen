
import random
import time
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi
from trafficgen.interactor import InteractionAction

import logging
logger = logging.getLogger(__name__)

class Amazon(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)

	def getRandomSearchTerm(self) -> str:
		return random.choice([
			"smartphone",
			"headphones",
			"laptop",
			"running shoes",
			"backpack",
			"sunglasses",
			"watch",
			"book",
			"coffee maker",
			"yoga mat",
			"blender",
			"printer",
			"table lamp",
			"wall art",
			"gaming chair",
			"face cream",
			"protein powder",
			"dog bed",
			"spice rack",
			"electric toothbrush",
			"hair dryer",
			"leggings",
			"frying pan",
			"handbag",
			"water bottle",
			"webcam",
			"tent",
			"jewelry",
			"board games",
			"car seat cover",
		])

	def cardCenterIsClickable(self, action: InteractionAction) -> bool:
		xcenter = (float(action.x) + float(action.xxe)) / 2.0
		ycenter = (float(action.y) + float(action.yye)) / 2.0
		return ycenter > 600 and ycenter < 2000 and xcenter > 0 and xcenter < 1077

	def goHome(self) -> None:
		logger.info("trying to return to amazon home screen...")
		self.emulator.interactor.clickOnCoordinate(130, 2080) # click on home

	def openApp(self, firstOpen=False) -> None:
		self.emulator.openApp("com.amazon.mShop.android.shopping")
		self.emulator.interactor.setCurrentApp("com.amazon.mShop.android.shopping")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		time.sleep(5)
		if firstOpen:
			logger.info("amazon first open, doing logins and setups")
			logger.info("amazon will ask us to switch to sg store any moment now...")
			for i in range(20):
				actions = self.emulator.interactor.getActions(stuckFactor=0)
				if "go to amazon.sg" in actions and "stay on amazon.com" in actions:
					actions["go to amazon.sg"].touch()
					break
				time.sleep(3)
			else:
				logger.info("cant see any amazon.sg prompt, continuing")
			time.sleep(2)
			self.emulator.interactor.clickOnButtonName("skip sign in")
			time.sleep(5)

	def addToCart(self):
		# assuming currently at the item page
		# scroll down maximum 5 times until we see an Add To Cart button
		for i in range(5):
			self.emulator.interactor.scrollDownHalfPage()
			actions = self.emulator.interactor.getActions()
			self.emulator.interactor.waitRandom(1,5)
			if "add to cart" in actions:
				logger.info("adding item to cart")
				actions["add to cart"].touch()
				break

	def shopTodaysDeals(self):
		logger.info("shopping for today's deals")
		self.emulator.interactor.clickOnCoordinate(130, 2080) # click on home
		self.emulator.interactor.clickOnCoordinate(130, 2080) # click on home
		self.emulator.interactor.clickOnButtonName("today's deals")
		for i in range(3):
			scrollOrNot = random.choice([True, False])
			if scrollOrNot:
				self.emulator.interactor.randomScrollDown()
				self.emulator.interactor.waitRandom()
		# click on a random item
		randomx = random.randint(80, 1000)
		randomy = random.randint(600, 1900)
		self.emulator.interactor.clickOnCoordinate(randomx, randomy)
		self.emulator.interactor.waitRandom()
		self.addToCart()
		self.emulator.interactor.backButton()
		self.emulator.interactor.backButton()

	def searchForRandomItem(self):
		logger.info("searching for a random item")
		searchTerm = self.getRandomSearchTerm()
		self.emulator.interactor.clickOnButtonName("search")
		self.emulator.interactor.clearTextField()
		self.emulator.interactor.typeInputText(searchTerm)
		self.emulator.interactor.enterKey()
		self.emulator.interactor.waitRandom()
		self.emulator.interactor.scrollSeveralTimes()
		# click on anything that has a dollar sign, if not keep scrolling
		while True:
			actions = self.emulator.interactor.getActions()
			clickableCards = {key: value for key, value in actions.items() if "$" in key and self.cardCenterIsClickable(value)}
			if not clickableCards:
				self.emulator.interactor.randomScrollDown()
				self.emulator.interactor.waitRandom()
				continue
			randomKey = random.choice(list(clickableCards.keys()))
			logger.info(f"clicking on a random item {randomKey}")
			actions[randomKey].touch()
			break
		self.emulator.interactor.waitRandom()
		self.addToCart()
		self.emulator.interactor.backButton()
		self.emulator.interactor.backButton()

	def clearCart(self):
		logger.info("clearing shopping cart")
		self.emulator.interactor.clickOnCoordinate(670, 2080) # click on carts
		while True:
			actions = self.emulator.interactor.getActions()
			if "delete" in actions:
				actions["delete"].touch()
				time.sleep(2)
				continue
			break
		self.emulator.interactor.clickOnCoordinate(130, 2080) # click on home

	def interact(self) -> None:
		while True:
			try:
				option = random.choices([
					self.searchForRandomItem,
					self.shopTodaysDeals,
					self.clearCart,
				], weights=[10, 10, 5])
				option[0]()
				self.emulator.interactor.waitRandom()
			except ErrNoAction as e:
				logger.info(f"ErrNoAction detected: {e}")
