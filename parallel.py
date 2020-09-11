import subprocess, time, random, os, multiprocessing, re
from copy import deepcopy


class Parallel(object):
	def __init__(self, p=1):
		self.max_cores = multiprocessing.cpu_count()
		self.p = int(min(p, self.max_cores))
		self.slots = [None for i in range(p)]
		self.command = [None for i in range(p)]
		self.cores = [None for i in range(p)]
		self.queue = []

	def add_cmd(self, cmd):
		if type(cmd) is list:
			new = deepcopy(cmd)
		elif type(cmd) is str:
			new = [cmd]
		else:
			raise TypeError(f"Unexpected type of command(s): {type(cmd)}")
		for i in range(0, len(new)):
			cmd[i] = re.sub(r"\s+", r" ", cmd[i])
			cmd[i] = cmd[i].strip().split(" ")
		self.queue.extend(cmd)

	def _get_proper_core(self):
		usage=psutil.cpu_percent(percpu=True)
		usage=[(i,usage[i]) for i in range(0,len(usage[i]))]
		random.shuffle(usage)
		usage.sort(key=lambda usage:usage[1])
		return usage[0][0]

	def run(self, assign_proc=True, log=False, shell=False):
		running = 0
		while True:
			try:
				for i in range(self.p):
					if self.slots[i] is None:
						if self.queue:
							cmd = self.queue.pop(0)
							self.command[i] = cmd
							print(">>> Running:", cmd)
							if info:
								self.slots[i] = subprocess.Popen(cmd, shell=shell)
							else:
								self.slots[i] = subprocess.Popen(
									cmd,
									stdout=subprocess.PIPE,
									stderr=subprocess.PIPE,
									shell=shell,
								)
							time.sleep(0.01)
							running += 1

							ready = list(set(range(0, self.max_cores)) - set(self.cores))
							index = random.choice(ready)
							self.cores[i] = index
							subprocess.run(
								["taskset", "-cp", f"{self._get_proper_core()}", f"{self.slots[i].pid}"],
								capture_output=False,
							)
					else:
						ret = self.slots[i].poll()
						if ret is not None:
							if ret != 0:
								print(f"Error {ret} with command {cmd}")
								output, error = self.slots[i].communicate()
								print(output)
								print(error)
								for j in range(self.p):
									if self.slots[j] is not None:
										self.slots[j].kill()
								return
							else:
								print("<<< Exited:", self.command[i])
								self.command[i] = None
								self.slots[i] = None
								self.cores[i] = None
								running -= 1
				if running == 0:
					break
				time.sleep(0.1)
			except KeyboardInterrupt:
				print('Killing...')
				for j in range(self.p):
					if self.slots[j] is not None:
						self.slots[j].kill()
				print('Killed by user')
