
import random
import time
from trafficgen import utils
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ErrNoAction, ExecUnstucked
from trafficgen.experiments.randomapp.appInteractor import AppInteractor, checkForBlockingUi

import logging
logger = logging.getLogger(__name__)

class CandyCrush(AppInteractor):
	def __init__(self, emulator: AndroidEmulator):
		super().__init__(emulator)

	def goHome(self) -> None:
		logger.info("trying to return to candycrush home screen...")
		self.emulator.interactor.closeApp()
		self.emulator.openApp("com.king.candycrushsaga")
		time.sleep(5)

	def openApp(self, firstOpen=False) -> None:
		self.emulator.openApp("com.king.candycrushsaga")
		self.emulator.interactor.setCurrentApp("com.king.candycrushsaga")
		self.emulator.interactor.addUnblocker(checkForBlockingUi)
		time.sleep(5)
		if firstOpen:
			logger.info("candycrush first open, doing logins and setups")
			self.emulator.interactor.clickOnButtonName("accept", retries=3)
			self.emulator.interactor.resetStuckCounter()

	def ensureAppIsOpened(self):
		def callback(result):
			if "com.king.candycrushsaga" in result.stdout:
				return True

		command = "adb shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'"
		isAppOpened = utils.executeShell(command, callbackSuccess=callback, captureOutput=True)
		if isAppOpened:
			return
		self.emulator.openApp(self.currentApp)
		time.sleep(2)
		raise ExecUnstucked

	def interact(self) -> None:
		try:
			time.sleep(10)
			self.ensureAppIsOpened()
			self.emulator.interactor.clickOnCoordinate(550, 1110)
			# assuming it will replay the tutorial every time
			time.sleep(13)
			self.ensureAppIsOpened()
			self.emulator.interactor.clickOnCoordinate(550, 2160)
			time.sleep(13)
			self.ensureAppIsOpened()
			self.emulator.interactor.clickOnCoordinate(550, 2160)
			self.emulator.interactor.resetStuckCounter()

			# start randomly swapping
			x1 = 310
			y1 = 940
			x2 = 770
			y2 = 1440
			while True:
				xstep = (x2-x1) / 4
				ystep = (y2-y1) / 4
				chosenxstep = random.randint(0, 4)
				chosenystep = random.randint(0, 4)
				chosenx = x1 + xstep*chosenxstep
				choseny = y1 + ystep*chosenystep
				direction = random.choice([(1,0), (0,1), (-1,0), (0,-1)])
				targetx = chosenx + xstep*direction[0]
				targety = choseny + ystep*direction[1]
				self.ensureAppIsOpened()
				logger.info("performing a candy swap")
				self.emulator.interactor.scroll(chosenx, choseny, targetx, targety, duration=150)
				self.emulator.interactor.resetStuckCounter()
				self.emulator.interactor.waitRandom()

		except ErrNoAction as e:
			logger.info(f"ErrNoAction detected: {e}")

