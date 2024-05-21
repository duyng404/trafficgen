

import random
import threading
import time
from trafficgen.emulator import AndroidEmulator
from trafficgen.exceptions import ExecUnstucked
from trafficgen.interactor import InteractionAction

import logging
logger = logging.getLogger(__name__)

def checkForBlockingUi(actions:dict[str, InteractionAction], texts:list[str]) -> bool:
	def waitRandom(self, noShorterThan: int = 0, noLongerThan: int = 0):
		duration = random.uniform(float(noShorterThan), float(noLongerThan))
		logger.info(f"idling for {duration}")
		time.sleep(duration)
	if "save" in actions and "not now" in actions:
		actions["not now"].touch()
		waitRandom(1,3)
		return True
	if "ok" in actions and "let us know" in actions and "try again later" in actions:
		actions["ok"].touch()
		waitRandom(1,3)
		return True
	if "android:id/autofill_dataset_picker" in actions and "close" in actions:
		actions["close"].touch()
		waitRandom(1,3)
		return True
	if "never" in actions and "save password" in actions:
		actions["never"].touch()
		waitRandom(1,3)
		return True
	if "close ad panel" in actions and "com.google.android.youtube:id/skip_ad_button" in actions:
		actions["close ad panel"].touch()
		actions["com.google.android.youtube:id/skip_ad_button"].touch()
		waitRandom(1,3)
		return True
	if "allow" in actions and "skip" in actions:
		actions["skip"].touch()
		waitRandom(1,3)
		return True
	if "got it" in actions:
		actions["got it"].touch()
		waitRandom(1,3)
		return True
	if "close" in actions and "select text and images to copy, share, and more" in texts:
		actions["close"].touch()
		waitRandom(1,3)
		return True
	if "close app" in actions and "wait" in actions:
		actions["close app"].touch()
		raise ExecUnstucked
	return False

class AppInteractor:
	def __init__(self, emulator: AndroidEmulator):
		self.emulator = emulator
		self.activity_profile = emulator.activity_profile
		self.app_freq_profile = emulator.config["randomapp"]["app_frequency_profile"]
		self.timeoutEvent: threading.Event = threading.Event()

	def goHome(self) -> None:
		pass

	def openApp(self) -> None:
		pass

	def interact(self) -> None:
		pass
