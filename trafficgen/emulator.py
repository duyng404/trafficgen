
import atexit
import os
import random
import re
import subprocess
import threading
import time
import utils
from trafficgen.interactor import Interactor
from trafficgen.exceptions import EmulatorFail

import logging
logger = logging.getLogger(__name__)

class AndroidEmulator:
	"""This class contains the basic operations with android emulator"""
	def __init__(self, config: dict[str, any]):
		self.config = config
		self.pcap_path = self.config["pcap_path"] if self.config["pcap_path"] else "./pcap"
		os.makedirs(self.pcap_path, exist_ok=True) # create folder and don't error if it already exists
		self.pcap_path = os.path.join(self.pcap_path, time.strftime('%Y%m%d%H%M', time.localtime())  + "-" + str(random.randint(1000, 9999)) + ".pcap")
		self.activity_profile: str = "medium"
		if "activity_profile" in self.config:
			self.activity_profile = self.config["activity_profile"]
		self.interactor = Interactor(self.activity_profile, self)
		self.process = None

	def start(self, wipeData=True, recordtraffic=True, pcapSuffix="") -> None:
		"""Starts the android emulator with the configured settings

		- wipeData (default True) set to True to start a new fresh emulator, deleting any existing user data. Set False to start from its existing snapshot instead.
		- recordTraffic (default True) set to False to avoid capturing traffic, overidding all configuration. If True, will fallback to the configuration whether to capture or not.
		- pcapSuffix (optional string) suffix to add to the pcap filename

		The function will waits until the emulator finishes starting up before returning.
		"""
		pcap_path = self.pcap_path
		if pcapSuffix:
			pcap_path = f"{pcap_path[:-5]}-{pcapSuffix}.pcap"
		command = "emulator {avd} {audio} {video} {gpu} {tcpdump} {wipedata}".format(
			avd=f"-avd {self.config['emulator']['avd']}" if "avd" in self.config.get("emulator", {}) else "",
			audio="-no-audio" if "disable_audio" in self.config.get("emulator", {}) and self.config["emulator"]["disable_audio"] else "",
			video="-no-window" if "disable_video" in self.config.get("emulator", {}) and self.config["emulator"]["disable_video"] else "",
			gpu="" if "disable_gpu_acceleration" in self.config.get("emulator", {}) and self.config["emulator"]["disable_gpu_acceleration"] else "-gpu host",
			tcpdump=f"-tcpdump {pcap_path}" if "tcpdump" in self.config.get("emulator", {}) and self.config["emulator"]["tcpdump"] and recordtraffic else "",
			wipedata="-wipe-data" if wipeData else "",
		)
		command = re.sub(r'\s+', ' ', command) # replace consecutive spaces to just one space
		logger.info(f"Launching emulator with command: {command}")
		try:
			self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			# Polls the state of the emulator and wait to finish startup. Wait at most 2 minutes (90 tries, 180 seconds)
			logger.info("Waiting until Emulator is ready ...")
			for i in range(90):
				try:
					output = subprocess.check_output(['adb', 'shell', 'getprop', 'sys.boot_completed']).decode('utf-8').strip()
					if output == '1':
						logger.info("Emulator is ready!")
						break
				except subprocess.CalledProcessError:
					pass
				time.sleep(2)  # Wait a bit before retrying.
			else:
				raise EmulatorFail("cannot start emulator") from e
		except subprocess.CalledProcessError as e:
			raise EmulatorFail("cannot start emulator") from e
		atexit.register(self.cleanup) # stops emulator when exiting
		return

	def stop(self) -> None:
		"""Stops the android emulator"""
		logger.info("Terminating emulator")
		self.process.kill()
		utils.executeShell(command="adb emu kill", retry=True)
		logger.info("It might take up to a minute for the emulator to fully shut down.")
		atexit.unregister(self.cleanup)

	def installApk(self, apkpath):
		logger.info(f"Installing apk {apkpath}")
		return utils.executeShell(f"adb install -g {apkpath}")

	def uninstallApp(self, packageName):
		logger.info(f"Uninstalling app {packageName}")
		return utils.executeShell(f"adb uninstall {packageName}", ignoreFailure=True)

	def openApp(self, packagename, mainactivity=None, domain=None):
		logger.info(f"Opening app: {packagename}")
		if mainactivity == None or mainactivity == 'None' or mainactivity == "":
			command = f"adb shell monkey -p {packagename} -c android.intent.category.LAUNCHER 1"
		else:
			command = f"adb shell am start -n '{packagename}/{mainactivity}'"
		if domain:
			command = command + f" -d '{domain}'"
		return utils.executeShell(command=command, retry=False)

	def showTapShowPointer(self):
		"""show tap location and pointer information on the emulator"""
		utils.executeShell("adb shell settings put system show_touches 1")
		utils.executeShell("adb shell settings put system pointer_location 1")

	def cleanup(self):
		logger.info("Performing emulator cleanup ...")
		self.stop()
