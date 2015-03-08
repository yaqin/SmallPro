import subprocess
import os, csv, codecs
import xml.etree.ElementTree as ET

#process = subprocess.Popen("sh
#/home/j/yaqin/tools/u/nlp/distrib/stanford-segmenter-2012-11-11/segment.sh
#ctb %s utf8 0 > %s"%(input_file,output_file),
#                                   shell=True, stdout=subprocess.PIPE,
#stderr=subprocess.STDOUT)

   


def getCH(im_file,output_dir):
    #im_file = "/home/j/yaqin/data/sms/119/data/translation/CHT_CMN_20120203.0000.eng.su.xml"
    #output_file = "/home/j/yaqin/tools/neural_net/mydata/tempch.txt"
    output_file = output_dir+"/"+im_file.split("/")[-1][:-3]+"chraw"
    process = subprocess.Popen(["grep","-Po","<message.*>\K.+(?=</message>)",im_file], stdout=subprocess.PIPE)
    line = process.communicate()[0]
    lines = line.split("\n")
    f = open(output_file,"w")
    for l in lines:
        f.write(l+"\n")
    f.close()

def getEN(im_file,output_dir):
    #im_file = "/home/j/yaqin/data/sms/119/data/translation/CHT_CMN_20120203.0000.eng.su.xml"
    #output_file = "/home/j/yaqin/tools/neural_net/mydata/tempen.txt"
    output_file = output_dir+"/"+im_file.split("/")[-1][:-3]+"enraw"
    process = subprocess.Popen(["grep","-Po","(?<=<body>).+(?=</body>)",im_file], stdout=subprocess.PIPE)
    line = process.communicate()[0]
    lines = line.split("\n")
    f = open(output_file,"w")
    for l in lines:
        f.write(l+"\n")
    f.close()

def parseXML(im_file):
    #tree = ET.parse(codecs.open(im_file,"r","utf8"))
    tree = ET.parse(im_file)
    root = tree.getroot()
    items = []
    for su in root.iter("su"):
        item = [root.get("id"),su.get("id")]
        for message in su.iter("message"):
            item.append(message.get("id"))
        for body in su.iter("body"):
            astr = body.text
            if astr == None:
                item.append("")
            else:
                item.append(astr)  
        if len(item) > 4:
            print item
            raw_input("next")
        items.append(item)
    return items
def getAllFiles(mypath):
    files = []
    for (dirpath, dirnames, filenames) in os.walk(mypath):
        for f in filenames:
            files.append(dirpath+"/"+f)
    return files

def parseXMLs(files,csvwriter):
    items = []
    for afile in files:
        items.extend(parseXML(afile))
    for aitem in items:
        csvwriter.writerow([x.encode("utf-8") for x in aitem])

def generateCSV(mypath):
    files = []
    lans = ["en","ch"]
    for lan in lans:
        csv_file = open(mypath+"/"+lan+".csv","w")
        csvwriter = csv.writer(csv_file)
        files = getAllFiles(mypath+"/"+lan)
        parseXMLs(files,csvwriter)
        csv_file.close()
def stanfordSegment(input_file, output_file):
    process = subprocess.Popen(["/home/j/yaqin/tools/stanford-segmenter-2012-11-11/nlp/distrib/stanford-segmenter-2012-11-11/segment.sh", "ctb",input_file,"UTF-8",output_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    process.communicate()

def berkeleyParse():
    print "run java -Xms10g -Xmx20g -cp ~/berkeleyParser.jar edu.berkeley.nlp.PCFGLA.BerkeleyParser -gr ~/berkeleyParser/1/grammar_bk/ctb6_1.gr -inputFile ch.csvtextonly.seg -outputFile ch.csvtextonly.bp"
 
def segmentCH(mypath,chcsv):
    csv_file = open(chcsv,"r")
    reader = csv.reader(csv_file)
    temp_file = open(chcsv+"textonly","w")
    ids = []
    for row in reader:
        ids.append(row[:-1])
        temp_file.write(row[-1]+"\n")
    temp_file.close()
    #stanfordSegment(chcsv+"textonly",chcsv+"textonly.seg")
    seg_csv = open(chcsv+".seg","w")
    sw = csv.writer(seg_csv)
    ti = open(chcsv+"textonly.seg","r")
    i = 0
    for l in ti:
        sw.writerow(ids[i]+[l.strip("\n")])
        i += 1
    seg_csv.close()

def generateCSV(chcsv,seg,parsefile,encsv,output_csv):
    csv_file = open(chcsv,"r")
    seg_file = open(seg,"r").readlines()
    parse_file = open(parsefile,"r")
    reader = csv.reader(csv_file)
    
    encsv_file = open(encsv,"r")
    er = csv.reader(encsv_file)    

    parse_csv = open(output_csv,"w")
    pw = csv.writer(parse_csv)
    ids = []
    ens = []
    for row in reader:
        ids.append(row)
    for e in er:
        ens.append(e)
    i = 0 
    for l in parse_file:
        if ids[i][0] != ens[i][0] or ids[i][1] != ens[i][1] or ids[i][2] != ens[i][2]:
            print ids[i][:-1]
            print ens[i][:-1]
            print "=="
            raw_input("next")
        if l.strip() == "(())":
            new_str2= "( (IP"
            for word in seg_file[i].strip("\n").split(" "):
                new_str2 += " (NN "+word+")"
            new_str2 += "))"
            print l, ids[i][-1],seg_file[i].strip("\n"),new_str2
            pw.writerow(ids[i][:-1]+[seg_file[i].strip("\n")]+[new_str2]+[ens[i][-1]]) 
        else:
            pw.writerow(ids[i][:-1]+[seg_file[i].strip("\n")]+[l.strip("\n")]+[ens[i][-1]])
        i += 1
    parse_csv.close()

if __name__ == "__main__":
    mypath = "/home/j/yaqin/data/sms"
    """read source and translation xml files,
        generate csv file"""
    #generateCSV(mypath)
    #segmentCH(mypath,mypath+"/ch.csv")   
    generateCSV(mypath+"/ch.csv",mypath+"/ch.csvtextonly.seg.nrm",mypath+"/ch.csvtextonly.bp",mypath+"/en.csv",mypath+"/all.csv")
