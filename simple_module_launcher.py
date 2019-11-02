from os import listdir, path

MODULES_PATH = "modules"


def get_module_list():
	mods = []

	for i in listdir(MODULES_PATH):
		if not i.endswith(".py"):
			continue
		try:
			mod = __import__(path.join(MODULES_PATH, i))
			assert "COMMANDS_EXPECTED" in mod.__dict__ and "action_function" in mod.__dict__
		except:
			continue
		mods.append((mod.COMMANDS_EXPECTED, mod))

	return mods
