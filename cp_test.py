from cp_interfaces import client, object_list

from routings import make_new_thread, get_active_thread

from random import randint

import requests
import json

from flask import request

class test_thread:

	def __init__(self, otype, oid, thread_id, user, session_cookie):

		if thread_id == "0":
			thread = make_new_thread({"otype": otype, "oid": oid}, user)
		else:
			thread = get_active_thread(thread_id)
		self.otype = otype
		self.oid = oid
		self.headers = {
		'Cookie': f'session={session_cookie}'
		}

		for key,value in thread.items():
			setattr(self, key, value)


	def add_message(self,message):
		params = {"otype": self.otype,
		"oid": self.oid,
		"thread_id": "0",
		"audience": json.dumps(self.audience),
		"tags": json.dumps(self.tags),
		"message": message}
		res = requests.post("http://localhost:5010/add_message", data=params, headers=self.headers)
		return res


def execute_test(user, session_cookie):

	lst = object_list("", user)
	obj = lst[randint(0,len(lst) - 1)]

	thread = test_thread(obj["id"]["id"][0], obj["id"]["id"][1], "0", user, session_cookie)
	return thread.add_message("Bu test modülünden eklenmiş bir mesajdır").json()