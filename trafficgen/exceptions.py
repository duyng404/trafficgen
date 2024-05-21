
class ExecTimeout(Exception):
    pass

class ShellExecFail(Exception):
    pass

class ErrNoAction(Exception):
	pass

class ExecStuck(Exception):
	pass

class ExecUnstucked(Exception):
    pass

class InteractFail(Exception):
    pass

class EmulatorFail(Exception):
    pass

class ExperimentFail(Exception):
    pass
