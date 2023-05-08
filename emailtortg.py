#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 15:47:01 2022

@author: cem
"""
from sampleintfcs import EMAIL_INTEGRATED, EMAIL_SENDER_ACC, EMAIL_SENDER_PWD

import email
from email.header import decode_header, make_header
from imaplib import IMAP4_SSL
from routings import add_rt_message
import re
import time

imap_server = "imap.gmail.com"
email_acc = EMAIL_SENDER_ACC
email_pwd = EMAIL_SENDER_PWD

SUBJ_PATTERN = "akvaryum paylaşım"
PREV_MAIL_REGEX = "On.*at.*wrote:"

def connect_imapserver():
    imap = IMAP4_SSL(imap_server)
    imap.login(email_acc, email_pwd) 
    imap.select("inbox")
    return imap       


def get_messages():
    messages = []
    imap = connect_imapserver()
    resp, mails = imap.search(None, "(UNSEEN)")
    print(mails[0].decode().split())
    for mail_id in mails[0].split():
        print("================== Start of Mail [{}] ====================".format(mail_id))
        resp, data = imap.fetch(mail_id, "(RFC822)")
        # email.charset.Charset(input_charset="utf-8")
        messages.append(email.message_from_bytes(data[0][1]))
    return messages
    
def correct_header(message, key):
    hdr, encoding = decode_header(message.get(key))[0]
    if encoding != None:
        hdr = hdr.decode(encoding)
    return hdr
    
def extract_email_addr(from_fld):
    ADDR_PATTERN = re.compile('<(.*?)>')
    addr = re.findall(ADDR_PATTERN, from_fld)
    if len(addr) > 0:
        return addr[0]
    
from bson.objectid import ObjectId


def process_emails():
    
    
    for message in get_messages():
        
        subj = correct_header(message, "Subject")
        frm = extract_email_addr(correct_header(message, "From"))

        # check if email is originated from a user and has the necessary signature
        if frm and frm != email_acc and subj.find(SUBJ_PATTERN) >= 0:
            oid = subj.split("&ID:")
            if len(oid) > 1:
                oid = oid[1]
            else:
                print("OID Missing in Subject")
                oid = None
                continue
 
            print("From       : {}".format(extract_email_addr(frm)))
            # print("To         : {}".format(message.get("To")))
            # print("Bcc        : {}".format(message.get("Bcc")))
            # print("Date       : {}".format(message.get("Date")))
            print("Subject    : {}".format(subj))
            print("OID        : {}".format(oid))
            
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(part.get_content_charset())
                    print("orig: ", body)
                    body = re.split(PREV_MAIL_REGEX, body)[0]
                    print("Trimmed: ", body)
                    add_rt_message(ObjectId(oid), frm, body, "email")
                    
while EMAIL_INTEGRATED:
    process_emails()
    time.sleep(30)                    
