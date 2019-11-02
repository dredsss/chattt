from socket import socket, SOCK_DGRAM, IPPROTO_UDP, timeout
from json import loads, dumps
from sys import argv


class ServerInterface:
	"""
	This is the base class for every Server instance.
	It contains main methods that must be implemented by the subclasses.
	"""
	def __init__(self, host="127.0.0.1", port=10300, modules: dict = None):
		self.socket = socket(type=SOCK_DGRAM)
		self.socket.bind((host, port))

		self.modules = modules  # It must be a list: List1[Tuple[Tuple1, Class]], where List1 - self.modules,
		# Tuple1 - list of commands that will be handled through this module
		self.nicknames = {}  # Dict{Address: Nickname}
		self.channels = {}  # Dict{Channel name: List[Addresses]}

	def getaddrbynick(self, nickname) -> tuple:  # It returns IP and port of the user by his nickname
		pass

	def check_permission(self, sender, **kwargs):  # Check if sender has permission to execute command in kwargs
		pass

	def receive_request(self, *args, **kwargs):  # Receive piece of data to be processed
		pass

	def send_raw(self, address, **kwargs):  # Send piece of data with no format
		pass

	def handle(self, *args, **kwargs):  # Handle 1 piece of data
		pass


class Code1v:
	ok = 1
	bad = 2
	incoming_channel_message = 3
	incoming_private_message = 4
	incoming_broadcast = 5
	incoming_system_message = 6
	unknown_command = 7


class Command1v:
	blank = 0
	set_nickname = 1
	forget_nickname = 2
	join_channel = 3
	leave_channel = 4
	send_private_message = 5
	send_channel_message = 6
	send_broadcast = 7
	get_user_list = 8
	get_channel_user_list = 9


class Server1v(ServerInterface):
	def getaddrbynick(self, nickname):
		for i in self.nicknames:
			if self.nicknames[i] == nickname:
				return i

	def check_permission(self, sender, **kwargs):
		for i in self.modules:
			if kwargs["command"] in i[0]:
				if i[1](sender, kwargs) is False:
					return False
		return True

	def send_raw(self, address, **kwargs):
		data = dumps(kwargs).encode()
		if len(data) > 1024:
			return
		self.socket.sendto(data, address)

	def receive_request(self):
		try:
			data, address = self.socket.recvfrom(1024)
			data = loads(data.decode())
			assert "command" in data and isinstance(data["command"], int)
		except (BlockingIOError, timeout, AssertionError):
			return None, None

		return data, address

	def handle(self):
		data, address = self.receive_request()

		if not data:
			return

		command = data["command"]

		if address not in self.nicknames:
			if command != Command1v.set_nickname and command != Command1v.blank and command != Command1v.forget_nickname:
				return self.send_raw(address, code=Code1v.bad)
			elif command == Command1v.set_nickname:
				if "nickname" not in data or data["nickname"] is None or not isinstance(data["nickname"], str):
					return self.send_raw(address, code=Code1v.bad)  # Irregular payload (nickname)
				nickname = data["nickname"]

				if nickname in self.nicknames.values() or address in self.nicknames:
					return self.send_raw(address, code=Code1v.bad)  # This nick is already taken/Already has a nick
				else:
					self.nicknames[address] = nickname
					return self.send_raw(address, code=Code1v.ok)
			elif command == Command1v.forget_nickname:
				return self.send_raw(address, code=Code1v.bad)  # can't forget what is not registered
			else:
				return self.send_raw(address, code=Code1v.ok)  # For blank command
		# Now main commands
		nickname = self.nicknames[address]

		if not self.check_permission(address, **data):
			return self.send_raw(address, code=Code1v.bad)

		if command == Command1v.set_nickname:
			return self.send_raw(address, code=Code1v.bad)
		elif command == Command1v.blank:
			return self.send_raw(address, code=Code1v.ok)
		elif command == Command1v.forget_nickname:
			self.nicknames.pop(address)
			return self.send_raw(address, code=Code1v.ok)
		elif command == Command1v.join_channel:
			if "channel_name" not in data or not isinstance(data["channel_name"], str) or not data["channel_name"]:
				return self.send_raw(address, code=Code1v.bad)  # Bad channel name
			if data["channel_name"] not in self.channels:
				self.channels[data["channel_name"]] = [address, ]
			else:
				self.channels[data["channel_name"]].append(address)
			return self.send_raw(address, code=Code1v.ok)
		elif command == Command1v.send_channel_message:
			if "channel_name" not in data or not isinstance(data["channel_name"], str) or not data["channel_name"]:
				return self.send_raw(address, code=Code1v.bad)  # Bad channel name
			if "message" not in data or not isinstance(data["message"], str) or not data["message"] or \
					len(data["message"]) > 300:
				return self.send_raw(address, code=Code1v.bad)  # Bad message
			for i in self.channels[data["channel_name"]]:
				self.send_raw(i, code=Code1v.incoming_channel_message, channel_name=data["channel_name"],
							  sender_nickname=nickname, message=data["message"])
			return self.send_raw(address, code=Code1v.ok)
		elif command == Command1v.leave_channel:
			if "channel_name" not in data or not isinstance(data["channel_name"], str) or not data["channel_name"]:
				return self.send_raw(address, code=Code1v.bad)  # Bad channel name
			if address in self.channels[data["channel_name"]]:
				self.channels[data["channel_name"]].pop(self.channels[data["channel_name"]].index(address))
				if not self.channels[data["channel_name"]]:
					self.channels.pop(data["channel_name"])
				return self.send_raw(address, code=Code1v.ok)
			return self.send_raw(address, code=Code1v.bad)  # Not in the channel's members
		elif command == Command1v.send_broadcast:
			if "message" not in data or not isinstance(data["message"], str) or not data["message"] or \
					len(data["message"]) > 300:
				return self.send_raw(address, code=Code1v.bad)  # Bad message
			for i in self.nicknames:
				self.send_raw(i, code=Code1v.incoming_broadcast, message=data["message"], sender_nickname=nickname)
			return self.send_raw(address, code=Code1v.ok)
		elif command == Command1v.send_private_message:
			if "message" not in data or not isinstance(data["message"], str) or not data["message"] or \
					len(data["message"]) > 300:
				return self.send_raw(address, code=Code1v.bad)  # Bad message
			if "receiver" not in data or not isinstance(data["receiver"], str) or not data["receiver"] or \
					data["receiver"] not in self.nicknames.values():
				return self.send_raw(address, code=Code1v.bad)  # Bad nickname
			self.send_raw(self.getaddrbynick(data["receiver"]), code=Code1v.incoming_private_message,
						  sender_nickname=nickname, message=data["message"])
			return self.send_raw(address, code=Code1v.ok)
		elif command == Command1v.get_user_list:
			return self.send_raw(address, users=list(self.nicknames.values()))
		elif command == Command1v.get_channel_user_list:
			if "channel_name" not in data or not isinstance(data["channel_name"], str) or not data["channel_name"]:
				return self.send_raw(address, code=Code1v.bad)  # Bad channel name
			if data["channel_name"] not in self.channels:
				return self.send_raw(address, users=[])
			return self.send_raw(address, users=[self.nicknames[i] for i in self.channels[data["channel_name"]]])
		else:
			return self.send_raw(address, code=Code1v.unknown_command)


if __name__ == "__main__":
	ip = "0.0.0.0"
	port = 10300
	modules = []
	try:
		if len(argv) == 3:
			ip = argv[1]
			port = argv[2]
		elif len(argv) == 4:
			ip = argv[1]
			port = argv[2]
			module_launcher = __import__(argv[3])
			modules = module_launcher.get_module_list()
		else:
			print("Usage: python3 server.py <IP> <port> [module launcher path]")
			exit(1)
	except:
		print("Error occurred while loading modules")
		exit(1)
	server = Server1v(ip, port, modules)
	print("Initialized server instance, starting main loop...")
	while True:
		server.handle()
