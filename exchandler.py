#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 16:06:53 2022

@author: cem
"""
from sampleintfcs import client

class CustExc(Exception):
    
    def __init__(self, exc_ID, lang):
        db = client.routeX
        doc = db.exceptions.find_one({"exc_ID": exc_ID,
                                      "lang": lang})
        if not doc: #exception undefined
            doc = db.exceptions.find_one({"exc_ID": "EnD",
                                          "lang": lang})

        self.exc_ID = exc_ID
        self.msg = doc["message"]
        super().__init__(self.msg)
            
    # def __str__(self):
    #     return f"{self.msg}"

