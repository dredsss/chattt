COMMANDS_EXPECTED = 1  # It is blank command


def action_function(instance, sender, *args, **kwargs):
	# "instance" - instance of Server class
	# sender - tuple of user engaged this command of (ip, port) format
	# *args - It is not used, but will be, so include it as well
	# **kwargs - all the payload is passed through it (or you can put some exact keyword args in case you expect only 1 command to be handled)
	if sender[0] == "127.0.0.1":
		return False  # So "blank" command is only working with non-local users
	else:
		return True
