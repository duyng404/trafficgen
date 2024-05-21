
import random
from threading import Event
import functools
import subprocess
import time
from trafficgen.exceptions import ShellExecFail, ExecTimeout

import logging
logger = logging.getLogger(__name__)

debugMode = True

def setup_utils(newDebugMode: bool) -> None:
	"""only used during code initialization to set the global debugMode variable in utils.py"""
	global debugMode
	debugMode = newDebugMode

def executeShell(command, retry=False, callbackSuccess=None, callbackFail=None, captureOutput=False, ignoreFailure=False) -> None:
	"""Execute a shell command, with various options.

	- specify retry=True to have the command retry (maximum 10 times) until successful
	- specify callbackSuccess as a callback function to be called when the command completed successfully
	- specify callbackFail as a callback function to be called when the command fails
	- specify captureOutput=True when used junction with any of the callbacks to have the callbacks be called with the result as the argument. E.g. callbackSuccess(result). Result is of type subprocess.CompletedProcess
	- specify ignoreFailure=True to disregard failure. This also makes the command runs only once without any retries.

	The function will:

	- return normally if the command completed successfully
	- raise a ShellExecFail exception if the command exited with a non-zero code or if the command encounter any exception during execution
	- raise a ShellExecFail exception if the command fails after 10 retries
	- having callback will override the above return behaviors
	"""
	triesLeft: int = 10
	logger.debug(f"executing command {command}")
	while True:
		try:
			result = subprocess.run(command, shell=True, check=True, capture_output=captureOutput or not debugMode, text=captureOutput )
			if result.returncode == 0:
				logger.debug("Command executed successfully.")
				if callbackSuccess:
					if captureOutput:
						return callbackSuccess(result)
					else:
						callbackSuccess()
				return
			else:
				logger.error(f"Error: command exited with non-zero return. {result.stderr.decode()}")
				if ignoreFailure:
					return
				if callbackFail and (not retry or triesLeft<=0):
					if captureOutput:
						return callbackFail(result)
					else:
						callbackFail()
						raise ShellExecFail("shell execution failed with non-zero code")
				if (not retry or triesLeft<=0):
					raise ShellExecFail("shell execution failed with non-zero code")
				time.sleep(2)
				triesLeft -= 1
		except subprocess.CalledProcessError as e:
			logger.debug(f"Error: exception while executing command: {e}")
			if ignoreFailure:
				return
			if callbackFail and (not retry or triesLeft<=0):
				if captureOutput:
					return callbackFail(result)
				else:
					callbackFail()
			if (not retry or triesLeft<=0):
				raise ShellExecFail("shell execution failed") from e
			time.sleep(2)
			triesLeft -= 1

def timeoutChecker():
	"""Decorator to check if an event is set before and after the function call.
	The event to watch for will be self.timeoutEvent, therefore this decorator can only be used for functions of any class that has that specific variable"""
	def decorator(func):
		@functools.wraps(func)
		def wrapper(self, *args, **kwargs):
			if self.timeoutEvent.is_set():
				raise ExecTimeout("Ran out of time for experiment.")
			result = func(self, *args, **kwargs)
			if self.timeoutEvent.is_set():
				raise ExecTimeout("Ran out of time for experiment.")
			return result
		return wrapper
	return decorator

def eventsTimer(timeoutEvents: list[Event], duration: int | float):
	"""Waits for `duration` and then call set() on all the events in `timeoutEvents`.

	Will detect if any event is set prematurely. In that case, will return without doing anything.
	"""
	while duration > 0.5:
		waitNext = 5 if duration >= 5 else duration
		duration = duration - waitNext
		time.sleep(waitNext)
		if any(event.is_set() for event in timeoutEvents):
			logger.info("event is set before timer expired.")
			return
	for event in timeoutEvents:
		event.set()
	logger.info("Time's up!")

def randomizeTimeLimit(timeLimit: int | float) -> float:
	"""Handy util function to randomize a given time duration to a value between 90% and 110% of the original value"""
	multiplier = random.uniform(0.9, 1.1)
	new_value = timeLimit * multiplier
	logger.info(f"Randomized time limit is {new_value}")
	return new_value
