# generic test modules for all applications
# uses object_list from the interface module
# import of object_list is from routings to 



# from cp_interfaces import client, object_list

from routings import make_new_thread, get_active_thread, client, object_list, ObjectId

from random import randint

import requests
import json

from datetime import datetime

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
		'Cookie': f'session={session_cookie}',
		'Accept': 'application/json'
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

	def add_audience(self, aud):
		params = {"otype": self.otype,
		"oid": self.oid,
		"thread_id": self._id,
		"audience": json.dumps(self.audience),
		"tags": json.dumps(self.tags),
		"slct-aud": aud["id"] + "||" + aud["name"] + "||" + aud["email"]}
		res = requests.post("http://localhost:5010/add_audience", data=params, headers=self.headers)
		return res


def execute_test(user, session_cookie):

	db = client.routeX # to write the test_results to db

	lst = object_list("", user)
	obj = lst[randint(0,len(lst) - 1)]

	otype = obj["id"]["id"][0]
	oid = obj["id"]["id"][1]

	#create a random thread adding a new message
	thread = test_thread(otype, oid, "0", user, session_cookie)
	result = thread.add_message("Bu test modülünden eklenmiş bir mesajdır").text
	result = json.loads(result)
	result["date"] = datetime.now()
	result["action"] = "Create Message"
	# check if the message is really added
	chk = db.routings.find_one({"_id": ObjectId(result["activethr"]["_id"])})
	result["success"] = True if chk else False # add any other checks here  	 
	success_list = [(result["action"], result["success"])]


	db.test_results.insert_one(result)


	#add a random person to audience

	person = result["activethr"]["authorized_users"][randint(0, len(result["activethr"]["authorized_users"] ) - 1)]
	while person in result["activethr"]["audary"]:
		person = result["activethr"]["authorized_users"][randint(0, len(result["activethr"]["authorized_users"] ) - 1)]

	thread = test_thread(otype, oid, result["activethr"]["_id"], user, session_cookie)
	result = thread.add_audience(person).text
	result = json.loads(result)
	result["date"] = datetime.now()
	result["action"] = "Add person to audience"

	doc = db.routings.find_one({"_id": ObjectId(result["activethr"]["_id"])})
	if doc and person in doc.get("audience", []):
		result["success"] = True
	else:
		result["success"] = False
	success_list.append((result["action"], result["success"]))


	db.test_results.insert_one(result)

	return success_list
