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
		try:
			res = json.loads(res.text)
		except:
			return res.text
		res["date"] = datetime.now()
		return res

	def add_audience(self, aud):
		params = {"otype": self.otype,
		"oid": self.oid,
		"thread_id": self._id,
		"audience": json.dumps(self.audience),
		"tags": json.dumps(self.tags),
		"slct-aud": aud["id"] + "||" + aud["name"] + "||" + aud["email"]}
		res = requests.post("http://localhost:5010/add_audience", data=params, headers=self.headers)
		try:
			res = json.loads(res.text)
		except:
			return res.text
		res["date"] = datetime.now()
		return res

	def del_audience(self, aud):
		params = {"otype": self.otype,
		"oid": self.oid,
		"thread_id": self._id,
		"audience": json.dumps(self.audience),
		"tags": json.dumps(self.tags),
		"slct-del-aud": aud["id"] 
		}
		res = requests.post("http://localhost:5010/del_audience", data=params, headers=self.headers)
		try:
			res = json.loads(res.text)
		except:
			return res.text
		res["date"] = datetime.now()
		return res

	def add_tag(self, tag):
		params = {"otype": self.otype,
		"oid": self.oid,
		"thread_id": self._id,
		"audience": json.dumps(self.audience),
		"tags": json.dumps(self.tags),
		"obj_id": json.dumps(tag)}
		res = requests.post("http://localhost:5010/add_tag", data=params, headers=self.headers)
		try:
			res = json.loads(res.text)
		except:
			return res.text
		res["date"] = datetime.now()
		return res

	def del_tag(self, tag):
		params = {"otype": self.otype,
		"oid": self.oid,
		"thread_id": self._id,
		"audience": json.dumps(self.audience),
		"tags": json.dumps(self.tags),
		"slct-del-tag": json.dumps(tag)}
		res = requests.post("http://localhost:5010/del_tag", data=params, headers=self.headers)
		try:
			res = json.loads(res.text)
		except:
			return res.text
		res["date"] = datetime.now()
		return res



def execute_test(user, session_cookie):

	db = client.routeX # to write the test_results to db

	lst = object_list("", user)
	obj = lst[randint(0,len(lst) - 1)]

	otype = obj["id"]["id"][0]
	oid = obj["id"]["id"][1]

	#create a random thread adding a new message
	thread = test_thread(otype, oid, "0", user, session_cookie)
	result = thread.add_message("Bu test modülünden eklenmiş bir mesajdır")

	if type(result) != dict or not result.get("activethr"):
		return result

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
	result = thread.add_audience(person)

	if type(result) != dict or not result.get("activethr"):
		return result

	result["action"] = "Add person to audience"

	doc = db.routings.find_one({"_id": ObjectId(result["activethr"]["_id"])})
	if doc and person in doc.get("audience", []):
		result["success"] = True
	else:
		result["success"] = False
	success_list.append((result["action"], result["success"]))

	db.test_results.insert_one(result)


	# now remove the person from the audience
	thread = test_thread(otype, oid, result["activethr"]["_id"], user, session_cookie)
	result = thread.del_audience(person)

	if type(result) != dict or not result.get("activethr"):
		return result

	result["action"] = "Delete person from audience"
	doc = db.routings.find_one({"_id": ObjectId(result["activethr"]["_id"])})
	if doc and person not in doc.get("audience", []):
		result["success"] = True
	else:
		result["success"] = False
	success_list.append((result["action"], result["success"]))

	db.test_results.insert_one(result)


	# add a random tag to the thread
	taglist = object_list("", user)
	tag = taglist[randint(0,len(taglist) - 1)]["id"]
	thread = test_thread(otype, oid, result["activethr"]["_id"], user, session_cookie)
	result = thread.add_tag(tag)

	if type(result) != dict or not result.get("activethr"):
		return result

	result["action"] = "Add tag to tags"
	#check if tag exists
	doc = db.routings.find_one({"_id": ObjectId(result["activethr"]["_id"])})
	if doc and tag in doc.get("tags", []):
		result["success"] = True
	else:
		result["success"] = False
	success_list.append((result["action"], result["success"]))

	db.test_results.insert_one(result)

	
	# delete the tag added in the previous step
	thread = test_thread(otype, oid, result["activethr"]["_id"], user, session_cookie)
	result = thread.del_tag(tag)

	if type(result) != dict or not result.get("activethr"):
		return result

	result["action"] = "Delete tag from tags"
	doc = db.routings.find_one({"_id": ObjectId(result["activethr"]["_id"])})
	if doc and tag not in doc.get("tags", []):
		result["success"] = True
	else:
		result["success"] = False
	success_list.append((result["action"], result["success"]))

	db.test_results.insert_one(result)



	return success_list
