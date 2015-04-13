import numpy
import codecs,nltk
import csv
import json
from pprint import pprint
from collections import defaultdict,OrderedDict
from nltk.corpus import BracketParseCorpusReader
from os import walk
import os,re
import cPickle
import xml.etree.ElementTree as ET
class Word():
    def __init__(self):
        self.suid = None
        self.fid = None
        self.within_sid = None
        self.label = None
        self.pid = None
        self.wid = None
def parseXML(im_file):
    """
    extract text from a xml file
    """
    tree = ET.parse(im_file)
    root = tree.getroot()
    text = root[0].text
    dic_start_tag = {}
    for tags in root[1]:
        start = int(tags.attrib["start"])
        pron = tags.tag
        dic_start_tag[start] = pron    
    dic_start_tag = sorted(dic_start_tag.items(), key=lambda dic: dic[0])
    newtext = text[:dic_start_tag[0][0]] + "#_"+dic_start_tag[0][1]
    for i in range(1, len(dic_start_tag)):
        newtext = newtext + text[dic_start_tag[i - 1][0] + 3:dic_start_tag[i][0]] + "#_"+ dic_start_tag[i][1]
    newtext += text[dic_start_tag[len(dic_start_tag) - 1][0] + 3:]

    text_list = newtext.split("\n")
    suid = 0
    within_sid = 0 
    pid = 0
    results = []
    for aline in text_list:
        if re.match("suid",aline):
            s,p = aline.split()
    	    suid = int(s.split("=")[1][1:])
            if int(p.split("=")[1]) != pid:
                within_sid = 0
            pid = int(p.split("=")[1])
        else:
            words = aline.split()
            wid = 0
            for i,a_word in enumerate(words):
                if re.match("\*",a_word):
                    if re.match("\*#",a_word):
                        label = a_word
                        li = i
                    continue
                cw = Word()
                cw.word = a_word
                cw.suid = suid
                cw.fid = None
                cw.within_sid = within_sid
                if i-1 == li:
                    cw.label = label
                    li = None
                cw.pid = pid
                cw.wid = wid
                print cw.word,cw.suid,cw.pid,cw.within_sid,cw.wid,cw.label
                results.append(cw)
                wid += 1
            within_sid += 1


def load_data():
    data_dir = "/Users/yaqin276/Code/SmallPro/data"
    train_dir = data_dir + "/Wang_Final"
    test_dir = data_dir + "/test"
    train_list = open(data_dir+"/train.filelist")
    test_list = open(data_dir+"/test.filelist")
    read_files(test_dir,test_list)
def read_files(data_dir,data_list):
    data_info = []
    for a_file in data_list:
        cur_file = data_dir+"/"+a_file.strip()
        print "process",a_file
        a_info = parseXML(cur_file)
        break
load_data()
