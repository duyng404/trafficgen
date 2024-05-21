
import pprint
import random
import re
import threading
import time
import xml.dom.minidom as xx
import os
from trafficgen.exceptions import ErrNoAction, ExecStuck, ShellExecFail, ExecUnstucked, ExecTimeout
import trafficgen.utils as utils

import logging
logger = logging.getLogger(__name__)

class InteractionAction:
	"""represents a clickable element on the screen"""
	def __init__(self, name:str, resid:str, x:str|int|float, y:str|int|float, xxe:str|int|float, yye:str|int|float):
		self.name = name
		self.resid = resid
		self.x = x
		self.y = y
		self.xxe = xxe
		self.yye = yye

	def touch(self):
		clickx = self.x
		clicky = self.y
		if int(self.xxe) != 0 and int(self.yye) != 0:
			clickx = (int(self.x) + int(self.xxe)) / 2.0
			clicky = (int(self.y) + int(self.yye)) / 2.0
		logger.info(f"clicking on x={clickx} y={clicky}")
		utils.executeShell(f"adb shell input tap {clickx:.2f} {clicky:.2f}")

class Interactor:
	"""contains a set of the most basic interaction operations with the android emulator"""
	def __init__(self, activity_profile: str, emulator):
		self.screenWidth = 0
		self.screenHeight = 0
		self.activity_profile = activity_profile
		self.timeoutEvent: threading.Event = threading.Event()
		self.stuckCounter: int = 0
		self.prevXML: str = ""
		self.savedXML: str = ""
		self.currentApp: str = ""
		self.currentAppActivity: str = ""
		self.currentAppAcitivityDomain: str = ""
		from trafficgen.emulator import AndroidEmulator
		self.emulator: AndroidEmulator = emulator
		self.unblockers: list[callable] = []

	def setCurrentApp(self, currentApp: str, currentActivity:str = None, currentDomain:str = None):
		"""sets the current app (and also current activity) (also the domain name if browsing with google chrome) so the interactor knows how to relaunch the app if sudden crash happens"""
		self.currentApp = currentApp
		self.currentAppActivity = currentActivity
		self.currentAppAcitivityDomain = currentDomain

	def addUnblocker(self, unblocker: callable):
		"""adding an unblocker callback function, which the interactor will call everytime an interaction happens, to detect and unblock any potential blocking UI.
		The call to the function will have two arguments: actions: dict[str, InteractionAction] and texts: list[str]"""
		self.unblockers.append(unblocker)

	def clearUnblockers(self):
		"""clear the current list of unblockers within the interactor"""
		self.unblockers.clear()

	def resetStuckCounter(self):
		"""resets the stuck counter to zero. Use this if you dont want the interactor to perform an unstucking behavior.
		E.g. when the screen does not change at all for any interaction and that's expected and doesn't count as stuck.
		More details about stuck counter in getActionsAndTexts()"""
		self.stuckCounter = 0

	@utils.timeoutChecker()
	def get_uidump(self) -> str:
		"""only used internally. run uiautomator dump to get an xml representation of all the screen elements"""
		logger.debug("Dumping UI ...")
		for i in range(12):
			try:
				utils.executeShell("adb shell uiautomator dump", captureOutput=True)
				utils.executeShell("adb pull sdcard/window_dump.xml", captureOutput=True)
				break
			except ShellExecFail as e:
				continue
		else:
			raise ExecStuck("tried too many times to get UI dump")
		dumpf = os.path.join(os.getcwd(),"window_dump.xml")
		logger.debug(f"Finished dumping UI to file {dumpf}")
		return dumpf

	def get_coordinates(self, coordinates: str) -> tuple:
		"""convert coordinate strings into proper coordinate values.
		Example input: '[11,22][33,44]'
		Example output: (11, 22, 33, 44)"""
		cc = coordinates.strip("[").strip("]").split("][")
		x = cc[0].split(",")[0]  # x_start
		y = cc[0].split(",")[1]  # y_start
		xxe = cc[1].split(",")[0] # x_end
		yye = cc[1].split(",")[1] # y_end
		return (x, y, xxe, yye)

	def get_texts(self, dumpf: str) -> list[str]:
		"""only used internally. from an xml file obtained from uiautomator dump, extract all the texts and description of all the elements"""
		textls: list[str] = []
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
			thename: str = ""
			if not thename:
				thename = elem.getAttribute("text")
			if not thename:
				thename = elem.getAttribute("content-desc")
			thename = thename.lower()
			enabled = elem.getAttribute("enabled")
			if len(thename) >= 1:
				if thename in textls:
					dupes: int = 0
					thename = thename + str(dupes)
					while True:
						if thename in textls:
							thename = thename[:-len(str(dupes))]
							dupes += 1
							thename = thename + str(dupes)
						else:
							break
				if enabled == "true":
					textls.append(thename)
		return textls

	def get_actions(self, dumpf: str, stuckFactor:int=2) -> dict[str, InteractionAction]:
		"""only used internally. from an xml file obtained from uiautomator dump, extract all the texts and description of all the elements"""
		actiondt: dict[str, InteractionAction] = dict()
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

		# check if stuck
		if stuckFactor:
			normalizedXML = dump.toxml()
			if self.prevXML == normalizedXML:
				self.stuckCounter += stuckFactor
			else:
				self.stuckCounter = 0
			self.prevXML = normalizedXML
			# if stuck, attempt to unstuck
			if self.stuckCounter >= 9:
				self.unstuck()

		textFieldCount: int = 0
		elemCount: int = 0
		nodes = dump.getElementsByTagName("node")
		# print(len(nodes))
		for elem in nodes:
			actionname: str = ""
			# print(elem.getAttribute("text") + " " + elem.getAttribute("class"))
			if elem.getAttribute("class")=="android.widget.EditText":
				actionname = f"TextField{textFieldCount}"
				textFieldCount += 1
			if elem.getAttribute("class")=="android.widget.Switch":
				actionname = f"WidgetSwitch{elemCount}"
				elemCount += 1
			if not actionname:
				actionname = elem.getAttribute("text")
			if not actionname:
				actionname = elem.getAttribute("content-desc")
			if not actionname:
				actionname = elem.getAttribute("resource-id")
			if not actionname:
				actionname = elem.getAttribute("class")
			actionname = actionname.lower()
			resid = elem.getAttribute("resource-id") #switch_btn
			classtype = elem.getAttribute("class")
			checkable = elem.getAttribute("checkable")
			clickable = elem.getAttribute("clickable")
			scrollable = elem.getAttribute("scrollable")
			longclickable = elem.getAttribute("long-clickable")
			coordinates = elem.getAttribute("bounds")
			coordinates = self.get_coordinates(coordinates)
			enabled = elem.getAttribute("enabled")
			focusable = elem.getAttribute("focusable")
			if len(actionname) >= 1:
				if actionname in actiondt:
					dupes: int = 0
					actionname = actionname + str(dupes)
					while True:
						if actionname in actiondt:
							actionname = actionname[:-len(str(dupes))]
							dupes += 1
							actionname = actionname + str(dupes)
						else:
							break
				if (checkable == "true" or clickable == "true" or scrollable == "true" or longclickable == "true" or classtype=="android.widget.Button" or resid=="post_vote_section") and enabled == "true":
					if int(coordinates[0]) == 0 and int(coordinates[1]) == 0:
						if elem.parentNode is not None:
							coordinates = self.get_coordinates(elem.parentNode.getAttribute("bounds"))
							if int(coordinates[0]) == 0 and int(coordinates[1]) == 0:
								continue
					actiondt[actionname] = InteractionAction(name=actionname, resid=resid, x=coordinates[0], y=coordinates[1], xxe=coordinates[2], yye=coordinates[3])
		logger.debug(f"Finished getting {len(actiondt)} actions from dump file")
		return actiondt

	def getActions(self, stuckFactor:int=2) -> dict[str, InteractionAction]:
		"""similar to getActionsAndTexts just without the texts"""
		return self.getActionsAndTexts(stuckFactor=stuckFactor)[0]

	def getActionsAndTexts(self, stuckFactor:int=2) -> tuple[dict[str, InteractionAction], list[str]]:
		"""obtain a list of all available elements that can be clicked on, and all readable texts on the current screen.
		stuckFactor (default 2) is an indicator to detect a stuck scenario. Each time the current screen is dumped for inspection (by calling this function),
		if the screen does not change since the last time it is inspected, the stuckCount will be increased by 2.
		When the stuckCount reaches 20, the emulator will be considered stuck, and the interactor will try to unstuck itself (by calling self.unstuck() -- see unstuck() for more info).
		You can change the stuckFactor if you want the stuck detector to be quicker or longer, or set to 0 to completely forgo the stuck checking.
		Note that the stuckCounter will also be increased when you call other interactor function like Scrolling, Tapping, etc. Use resetStuckCounter() if you want a guarantee way to avoid the unstucker.
		"""
		dumpf = self.get_uidump()
		texts = self.get_texts(dumpf)
		actions = self.get_actions(dumpf, stuckFactor)
		for unblocker in self.unblockers:
			self.ensureAppIsOpened()
			executed = unblocker(actions, texts)
			if executed:
				dumpf = self.get_uidump()
				texts = self.get_texts(dumpf)
				actions = self.get_actions(dumpf, stuckFactor)
		return (actions, texts)

	def dumpActions(self) -> None:
		"""print out all clickable actions to the stdout"""
		actions = self.getActions()
		for action in actions:
			print(f"- {action} : {actions[action].x} {actions[action].y} {actions[action].xxe} {actions[action].yye}")

	def dumpTexts(self) -> None:
		"""print out all readable texts to the stdout"""
		dumpf = self.get_uidump()
		texts = self.get_texts(dumpf)
		for text in texts:
			print(f"- {text}")

	def saveDump(self) -> None:
		"""Get a UI dump, and remember it. Use in conjunction with compareDump() to detect UI changes between a series of interactions"""
		dumpf = self.get_uidump()
		if not os.path.isfile(dumpf):
			logger.error("Failed to obtain UI dump for APK. Exiting UI interaction")
			return {}
		dump = xx.parse(dumpf)
		if not dump:
			logger.error("Cannot parse dumped UI for some reason")
			return {}
		self.savedXML = dump.toxml()

	def compareDump(self) -> bool:
		"""returns true if ui has changed since saveDump(), false if not"""
		dumpf = self.get_uidump()
		if not os.path.isfile(dumpf):
			logger.error("Failed to obtain UI dump for APK. Exiting UI interaction")
			return {}
		dump = xx.parse(dumpf)
		if not dump:
			logger.error("Cannot parse dumped UI for some reason")
			return {}
		normalizedXML = dump.toxml()
		if self.savedXML != normalizedXML:
			return True
		return False

	def unstuck(self):
		"""attempt to unstuck the emulator by clicking back until we arrive at the android home screen, then relaunch the currentApp. If currentApp is not specified, will stay at the android home screen"""
		logger.info("we are probably stuck, unstucking ...")
		while True:
			dumpf = self.get_uidump()
			actions = self.get_actions(dumpf, stuckFactor=0)
			if "search" in actions and "apps list" in actions:
				break
			self.backButton()
		if self.currentApp:
			self.emulator.openApp(self.currentApp, mainactivity=self.currentAppActivity, domain=self.currentAppAcitivityDomain)
			time.sleep(2)
		raise ExecUnstucked

	@utils.timeoutChecker()
	def ensureAppIsOpened(self):
		"""only used internally. check if the specified currentApp is the currently opened App. If not, relaunch it. Used to check for random app crashes or sudden app switches (eg, accidental click on ads)"""
		if not self.currentApp:
			return
		def callback(result):
			if self.currentApp in result.stdout:
				return True

		for i in range(20):
			command = "adb shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'"
			isAppOpened = utils.executeShell(command, callbackSuccess=callback, captureOutput=True)
			if isAppOpened:
				break
			self.emulator.openApp(self.currentApp)
			time.sleep(2)
		else:
			raise ExecStuck("unable to open app")

	@utils.timeoutChecker()
	def clickOnCoordinate(self, x: str | int, y: str | int, xxe: str | int = 0, yye: str | int = 0) -> None:
		clickx = x
		clicky = y
		if xxe != 0 and yye != 0:
			clickx = (int(x) + int(xxe)) / 2.0
			clicky = (int(y) + int(yye)) / 2.0
		logger.info(f"clicking on x={clickx} y={clicky}")
		utils.executeShell(f"adb shell input tap {clickx:.2f} {clicky:.2f}")

	def clickOnButtonName(self, buttonName: str, retries: int = 2) -> None:
		"""obtain an UI dump, then look at the list of clickable element for a matching `buttonName`, and click on it"""
		attempt = 0
		while attempt < retries:
			dumpf = self.get_uidump()
			actions = self.getActions(dumpf)
			if buttonName in actions:
				logger.info(f"clicking on button {buttonName}")
				return actions[buttonName].touch()
			else:
				logger.error(f"button not found: {buttonName}")
				attempt += 1
				time.sleep(2)
		raise ErrNoAction(f"button not found: {buttonName}")

	def clickOnRandomButtonName(self, buttonName: str) -> None:
		"""similar to clickOnButtonName, but if there are many buttons with the same prefix, click on a random one. E.g. video video0 video1 video2 -> will click on a random video"""
		dumpf = self.get_uidump()
		actions = self.getActions(dumpf)
		clickables = {key: value for key, value in actions.items() if key.startswith(buttonName)}
		if not clickables:
			raise ErrNoAction(f"no clickable {buttonName} button in view")
		randomKey = random.choice(list(clickables.keys()))
		logger.info(f"clicking on button {randomKey}")
		return actions[randomKey].touch()

	@utils.timeoutChecker()
	def typeInputText(self, text: str) -> None:
		self.getActions() # ensure we are not blocked or stuck
		escapedSpaces = text.replace(" ","\\ ")
		utils.executeShell(f"adb shell input text '{escapedSpaces}'")

	@utils.timeoutChecker()
	def scroll(self, x, y, xxe, yye, duration="3000"):
		nulllst = ["None", None]
		if not (x in nulllst and y in nulllst and xxe in nulllst and yye in nulllst):
			self.getActions() # ensure we are not blocked or stuck
			utils.executeShell(f"adb shell input swipe {x} {y} {xxe} {yye} {duration}")
		return

	def scrollDownHalfPage(self) -> None:
		w, h = self.getScreenWidthHeight()
		logger.info("scrolling down half page")
		self.scroll(w/2, h*3/4, w/2, h*1/4, duration="400")

	def scrollUpHalfPage(self) -> None:
		w, h = self.getScreenWidthHeight()
		logger.info("scrolling up half page")
		self.scroll(w/2, h*1/4, w/2, h*3/4, duration="400")

	def swipeFromLeft(self) -> None:
		w, h = self.getScreenWidthHeight()
		logger.info("swiping in from left edge")
		self.scroll('0', h/2, w/2, h/2, duration='300')

	def scrollDownLongFlick(self) -> None:
		w, h = self.getScreenWidthHeight()
		logger.info("scrolling down long flick")
		self.scroll(w/2, h*3/4, w/2, h/2, duration="60")

	def scrollDownShortFlick(self) -> None:
		w, h = self.getScreenWidthHeight()
		logger.info("scrolling down short flick")
		self.scroll(w/2, h*3/4, w/2, h/2, duration="80")

	def scrollDownFullPage(self) -> None:
		w, h = self.getScreenWidthHeight()
		logger.info("scrolling down full page")
		self.scroll(w/2, h*5/7, w/2, h*2/7, duration="400")

	def randomScrollDown(self) -> None:
		option = random.choices([
			self.scrollDownLongFlick,
			self.scrollDownShortFlick,
			self.scrollDownHalfPage,
			self.scrollDownFullPage,
		], weights=[3, 5, 3, 4])
		option[0]()

	def scrollSeveralTimes(self) -> None:
		repeats = random.randint(1, 2)
		if self.activity_profile == "medium":
			repeats = random.randint(2, 6)
		if self.activity_profile == "high":
			repeats = random.randint(4, 10)
		for i in range(repeats):
			scrollOrNot = random.choice([True, False])
			if scrollOrNot:
				self.randomScrollDown()
				self.waitRandom()

	@utils.timeoutChecker()
	def homeButton(self) -> None:
		logger.info("tapping on home button")
		utils.executeShell("adb shell input keyevent KEYCODE_HOME")

	@utils.timeoutChecker()
	def recentAppButton(self) -> None:
		logger.info("tapping on recent app button")
		utils.executeShell("adb shell input keyevent KEYCODE_APP_SWITCH")

	@utils.timeoutChecker()
	def backButton(self) -> None:
		logger.info("tapping on back button")
		utils.executeShell("adb shell input keyevent KEYCODE_BACK")

	@utils.timeoutChecker()
	def enterKey(self) -> None:
		logger.info("enter key")
		utils.executeShell("adb shell input keyevent KEYCODE_ENTER")

	@utils.timeoutChecker()
	def tabKey(self) -> None:
		logger.info("tab key")
		utils.executeShell("adb shell input keyevent KEYCODE_TAB")

	def getScreenWidthHeight(self) -> None:
		"""get the screen dimensions of the currently running android emulator"""
		if not self.screenWidth or not self.screenHeight:
			def callback(result):
				match = re.search(r'(\d+)x(\d+)', result.stdout)
				if match:
					width, height = map(int, match.groups())
					return width, height
				else:
					logger.error("Failed to parse screen size from ADB output.")
					return None, None

			command = "adb shell wm size"
			self.screenWidth, self.screenHeight = utils.executeShell(command, callbackSuccess=callback, captureOutput=True)

		return self.screenWidth, self.screenHeight

	@utils.timeoutChecker()
	def waitRandom(self, noShorterThan: int = 0, noLongerThan: int = 0):
		if not noShorterThan or not noLongerThan:
			if self.activity_profile == "low":
				noShorterThan = 7
				noLongerThan = 20
			if self.activity_profile == "medium":
				noShorterThan = 2
				noLongerThan = 10
			if self.activity_profile == "high":
				noShorterThan = 1
				noLongerThan = 4
		duration = random.uniform(float(noShorterThan), float(noLongerThan))
		self.getActions(stuckFactor=0) # ensure we are not blocked
		logger.info(f"idling for {duration}")
		# staggered waits: wait for 10 seconds at a time, checking timeout in the middle
		while duration > 0.5:
			waitNext = 10 if duration >= 10 else duration
			duration = duration - waitNext
			time.sleep(waitNext)
			if self.timeoutEvent.is_set():
				raise ExecTimeout("Ran out of time for experiment.")

	def closeApp(self):
		logger.info("closing app")
		self.emulator.interactor.recentAppButton()
		time.sleep(1)
		w, h = self.getScreenWidthHeight()
		utils.executeShell(f"adb shell input swipe {w/2} {h*3/4} {w/2} {h/2} {80}")
		time.sleep(1)
		self.emulator.interactor.homeButton()
		time.sleep(1)

	def clearTextField(self):
		logger.info("clearing text field")
		utils.executeShell("adb shell input keyevent KEYCODE_MOVE_END")
		utils.executeShell("adb shell input keyevent --longpress $(printf 'KEYCODE_DEL %.0s' {1..200})")
