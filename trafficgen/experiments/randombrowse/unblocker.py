
import random
import time
from trafficgen.exceptions import ExecUnstucked
from trafficgen.interactor import InteractionAction

import logging
logger = logging.getLogger(__name__)

POPUP_KEYWORDS: dict[str, list[str]] = {
	"google.com": [
        "stay signed out",
		"no thanks",
	],
    "*": [
		"accept all",
		"同意",
		"accept & continue",
		"no thanks",
		"start",
		"enter",
		"i agree",
		"ok",
		"skip",
		"allow",
		"continue",
		"agree",
		"got it",
		"got it!",
		"yes",
		"continue in browser",
		"i got it",
		"always",
		"agree & continue",
		"retry",
		"only this time",
		"yes i am 18+",
		"accept all cookies",
		"accept cookies",
		"not now",
		"maybe later",
		"yes, i am happy",
		"i accept",
		"accept all",
		"allow all cookies",
		"allow all",
		"accept cookies & continue",
		"cancel",
		"accept & close",
		"i am 18 or older",
		"applica",
		"accetta e continua",
		"near me",
		"jai compris",
		"jeg forstår",
		"accetta",
		"accetta tutti",
		"chiudi video",
		"chiudi",
		"__ 滿 18 歲, 請按此 __"
	]
}

def checkForBlockingUi(actions:dict[str, InteractionAction], texts:list[str]) -> bool:
	def waitRandom(self, noShorterThan: int = 0, noLongerThan: int = 0):
		duration = random.uniform(float(noShorterThan), float(noLongerThan))
		logger.info(f"idling for {duration}")
		time.sleep(duration)
	if "allow" in actions and "block" in actions and any("wants to use your device's location" in key for key in texts):
		actions["block"].touch()
		waitRandom(1,3)
		return True
	if "allow" in actions and "block" in actions and any("wants to use your microphone" in key for key in texts):
		actions["block"].touch()
		waitRandom(1,3)
		return True
	if "download" in actions and "cancel" in actions and any("download file" in key for key in texts):
		actions["cancel"].touch()
		waitRandom(1,3)
		return True
	return False
