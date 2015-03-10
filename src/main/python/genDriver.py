import gensim,numpy,scipy
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
#cmodel = gensim.models.word2vec.Word2Vec.load_word2vec_format('/home/j/yaqin/tools/word2vec/gigaword.bin',binary=True)

def readCSV(annotation):
    """
    read the annotation csv file, 
    """
    with open(annotation, 'rb') as csvfile:
        anno_reader = csv.reader(csvfile)
        entity_dict = defaultdict(lambda:defaultdict())
        for row in anno_reader:
            id, annotation_type, annotation_value, document, who, token, status, sentence, date_created, software_version= row
            document = document.split("/")[-1]
            if document == "DOCUMENT" or not re.match("chtb",document):
                print row
                continue
            entity_dict[(document,int(sentence),int(token))][who] = annotation_value
    
  
    illegal_dict = defaultdict()
    legal_dict = defaultdict()
    for index in entity_dict:
        if "gold" in entity_dict[index]:
            legal_dict[index] =  entity_dict[index]["gold"]
        else:
            temp = defaultdict(lambda:0)
            max_count = 0
            if len(entity_dict[index]) == 1:
                illegal_dict[index] = entity_dict[index].values()[0]

            for annotator in entity_dict[index]:
                temp[entity_dict[index][annotator]] += 1

            max_count = max(temp.values())
            for a in temp:
                if temp[a] == max_count and temp[a] >= 2:
                    legal_dict[index] = a
            
            if index not in legal_dict:
                if "ebaran" in entity_dict[index]:
                    illegal_dict[index] = entity_dict[index]["ebaran"]
                else:
                    illegal_dict[index] = entity_dict[index].values()[0]
            
    print sum([len(entity_dict[x].values()) for x in entity_dict]),len(entity_dict),len(illegal_dict),len(legal_dict),len(set(legal_dict.values()))
    to_write = OrderedDict(sorted(legal_dict.items()+illegal_dict.items()),
                           key=lambda t: (t[0][0],t[0][1],t[0][2]))
    return to_write

def readTask(task_dir):
    """
    read the task file -- to get following word and head word positions
    index_dict: key -- (filename, sentence index, word index)
                value -- head index
    """
    index_dict = defaultdict(lambda:[]) 
    for (dirpath, dirnames, filenames) in walk(task_dir):
        for afile in filenames: 
            atask_file = os.path.join(dirpath,afile)
            #atask_file = dirpath + "/" + afile
            with open(atask_file,"r") as atask:
                for line in atask:
                    fname, sid, wid, hid = line.strip().split()[:4]
                    fname = fname.split("/")[-1]
                    index_dict[(fname,int(sid),int(wid))].append(int(hid))
    return index_dict

def writeCSV(output,to_write):
    with open(output, 'wb') as csvfile:
        anno_writer = csv.writer(csvfile)
        for k in to_write:
            document,sentence,token = k
            annotation_value = to_write[k]
            anno_writer.writerow([document,sentence,token,annotation_value])
            #anno_writer.writerow([document,sentence,token] + [x[0]+"_"+x[1] for x in annotation_value])


def getWVFeat(**kwargs):
    cmodel = kwargs["cmodel"]
    sent = kwargs["sent"]
    i_index = kwargs["iid"]
    j_index = kwargs["jid"]
    i_word = sent[i_index]
    j_word = sent[j_index]
    wvf = numpy.array([])
    """current word vecotr"""
    try:
        wvf = numpy.append(wvf,cmodel[i_word])
    except:
        print "no word vecotr for i word", i_word
        wvf = numpy.append(wvf,numpy.zeros(300))
    """head word vecotr"""
    try:
        wvf = numpy.append(wvf,cmodel[j_word])
    except:
        print "no word vector for j word", j_word
        wvf = numpy.append(wvf,numpy.zeros(300))
        
    """prev word vector"""
    if i_index != 0:
        try:
            wvf = numpy.append(wvf,cmodel[sent[i_index-1]])
        except:
            print "no word vector for prev word",sent[i_index-1]
            wvf = numpy.append(wvf,numpy.zeros(300))
    else:
        wvf = numpy.append(wvf,cmodel["BOS"])
    """next word vector"""
    if i_index < len(sent)-1:
        try:
            wvf = numpy.append(wvf,cmodel[sent[i_index+1]])
        except:
            print "no word vector for next word", sent[i_index+1]
            wvf = numpy.append(wvf,numpy.zeros(300))
    else:
        wvf = numpy.append(wvf,cmodel["EOS"])
    return wvf
    
def getOneHotFeat(**kwargs):
    sent = kwargs["sent"]
    i_index = kwargs["iid"]
    j_index = kwargs["jid"]
    i_word = sent[i_index]
    j_word = sent[j_index]
    ohf = numpy.array([])
    """if it's the first word"""
    if i_index == 0:
        ohf = numpy.append(ohf,[0,1])
    else:
        ohf = numpy.append(ohf,[1,0])    
    """if i and j are the same word"""
    if i_index == j_index:
        ohf = numpy.append(ohf,[0,1])
    else:
        ohf = numpy.append(ohf,[1,0])
    return ohf

def readSMS(**kwargs):
    sms_ch_csv = kwargs["sms_ch_csv"]
    csv_file = open(sms_ch_csv,"rb")
    reader = csv.reader(csv_file)
    
    feat_csv = kwargs["sms_ch_feat"]
    feat_file = open(feat_csv,"wb")
    fw = csv.writer(feat_file)
    count = 0
    for row in reader:
        print "sms",count
        count += 1
        aparse = nltk.tree.Tree(row[-2])
        sent_feat = processAsentence(aparse,**kwargs)
        for afeat in sent_feat:
            fw.writerow(row[:-2]+afeat)
    feat_file.close()

def readStagesTrain(**kwargs):
    auto_corpus = kwargs["stages_train_corpus"]
    filelist_id = "00"
    feat_csv = kwargs["stages_train_feat"]
    feat_file = open(feat_csv+filelist_id,"wb")
    fw = csv.writer(feat_file) 
    
    docs = open(kwargs["stages_train_filelist"]+filelist_id)
       
    count = 0
    for fid in docs:
        print fid
        treeid = 0
        for aline in codecs.open(auto_corpus+"/"+fid.strip("\n"),"r",encoding="gb18030"):
            atree = nltk.tree.Tree(aline)
            sent_feat = processAsentence(atree,**kwargs)
            for afeat in sent_feat:
                #print count
                count += 1
                fw.writerow([fid,treeid]+afeat)
            treeid += 1
    feat_file.close()


def readAnnotatedData(annotation_dict,task_dict,**kwargs):
    cmodel = kwargs["cmodel"]
    corpus = kwargs["corpus"]
    auto_corpus = kwargs["auto_corpus"]
    feat_label_file = kwargs["ctb_feat_label"]
    file_pattern = r".*\.fid\.head\.idt"
    auto_pattern = r".bps"
    tree_corpus = BracketParseCorpusReader(corpus,file_pattern)
    auto_tree_corpus = BracketParseCorpusReader(auto_corpus,auto_pattern)
    feat_csv = kwargs["ctb_feat_label"]
    feat_file = open(feat_csv,"wb")
    fw = csv.writer(feat_file)
    nohead = 0
    """
    read annotation dict -- key: document,sentence,token; value: annotation_value
    task_dict -- key: document,sentence,token; value: [j_id]
    generate doc_dict -- key: document; value: {sentenc:{(i_id,j_id):annotation_value}} 
    """
    doc_dict = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:None)))
    for k in annotation_dict:
        if k == "key":
            continue
        document,sentence,token = k
        annotation_value = annotation_dict[k]
        if k not in task_dict:
            nohead += 1
            head = token
        else:
            if len(task_dict[k]) > 1 :
                print "more than one head?",k,task_dict[k]
            head = task_dict[k][0]
        doc_dict[document][sentence][(token,head)] = annotation_value
    sorted_doc_dict = OrderedDict(sorted(doc_dict.items(),key=lambda t:t[0]))
    print "nohead",nohead
    count = 0
    for d in sorted_doc_dict:
        print d
        fid = d.split(".")[0]+".fid.head.idt"
        trees = tree_corpus.parsed_sents(fileids = fid)
        autotrees = tree_corpus.parsed_sents(fileids = d.split(".")[0]+".bps")
        for treeid,atree in enumerate(trees):
            tt_dict = defaultdict()
            t1 = 0
            for t2 in range(len(atree.pos())):
                if not re.match("-",atree.pos()[t2][1]):
                    tt_dict[t1] = t2
                    t1 += 1
            if treeid in sorted_doc_dict[d]:
                #sent_feat = processAsentence(atree,**kwargs)
                sent_feat = processAsentence(autotrees[treeid],**kwargs)
                for afeat in sent_feat:
                    i_id, j_id = afeat[:2]
                    label = ["NPRO","NPRO"]
                    if (i_id,j_id) in sorted_doc_dict[d][treeid]:
                        ec_type,ec_pos = atree.pos()[tt_dict[i_id]-1]
                        if not re.match("-",ec_pos):
                            print d,tree.leaves(),ec_pos,tt_dict
                            raw_input("next")         
                        label = [ec_type,sorted_doc_dict[d][treeid][(i_id,j_id)]]
                    print count
                    count += 1
                    if afeat[0] != i_id or afeat[1] != j_id:
                        print afeat[:2],i_id,j_id
                        raw_input("id messed up")
                    fw.writerow([d,treeid,i_id,j_id]+label+afeat[2:])
    feat_file.close()
                                    
    

def processAsentence(atree,**kwargs):
    #i_dict = {"SB":2,"M":3,"PN":5,"JJ":6,"LB":6,"CC":11,"OD":14,"NR":15,"MSP":21,"CD":32,"CS":47,"DT":51,"PU":53,"BA":57,"VC":59,"VA":63,"NN":68,"VE":85,"NT":259,"P":938,"AD":1046,"VV":3038}
    #j_dict = {"AD":1,"NN":2,"CD":2,"P":2,"PU":3,"SB":4,"LB":9,"BA":76,"VA":111,"VC":111,"VE":244,"VV":5314}
    terminals = [atree.leaf_treeposition(i) for i in range(len(atree.pos())) if not re.match("-",atree.pos()[i][1])]
    kwargs["sent"] = [atree[x].encode("utf-8") for x in terminals]
    #print "".join(atree.leaves())
    i_dict = kwargs["i_dict"]
    j_dict = kwargs["j_dict"]
    sent_feat = []
    for i_id, i_tpos in enumerate(terminals):
        i_word= atree[i_tpos]
        i_pos = atree[i_tpos[:-1]].node
        i_pos = i_pos.split("-")[0]
        if i_pos in i_dict:
            j_id = i_id
            while j_id < len(terminals):
                j_tpos = terminals[j_id]
                j_pos = atree[j_tpos[:-1]].node
                j_pos = j_pos.split("-")[0]
                if j_pos in j_dict and inDomain(atree,i_tpos,j_tpos):
                    j_word = atree[j_tpos]
                    kwargs["iid"] = i_id
                    kwargs["jid"] = j_id
                    wvf = getWVFeat(**kwargs)
                    ohf = getOneHotFeat(**kwargs)
                    sent_feat.append([i_id,j_id]+wvf.tolist()+["onhotfeat"]+ohf.tolist())
                j_id +=1
    return sent_feat

def inDomain(atree,i_node,j_node):
    dom_node = dominateNode(i_node,j_node)
    if not (outOfDomain(atree,i_node, dom_node) or outOfDomain(atree,j_node,dom_node)):
        return True
    return False
    

def dominateNode(anodeposition, bnodeposition):
    #fiven two nodes, r  eturn the dominate node
    i = 0
    while i < len(anodeposition) and i < len(bnodeposition) and bnodeposition[i] == anodeposition[i]:
        i += 1
    return anodeposition[:i]

def outOfDomain(atree,child, ancestor):
    #is the ancestor out of the clause domain of the child
    label = ""
    cur_node = child
    while len(cur_node) >= 0 and cur_node != ancestor:
        if isinstance(atree[cur_node],unicode) or isinstance(atree[cur_node],str):
            label = atree[cur_node]
        else:
            label = atree[cur_node].node.split("-")[0]
        if label == "IP" or label == "CP":
            if len(cur_node) >= 0 and atree[cur_node[:-1]].node.split("-")[0] != "CP":
                return True
        if len(cur_node) == 0:
            break
        cur_node = cur_node[:-1]
    return False
                         
    
    
#def generateCTBTheanoFormat(csv):
       
def generateSMSTheanoFormat(syncsv,wvcsv):
    """
    input -- a cvs file with description
    output -- apickled file including label(numpy.array),feat(numpy.array)
    """
    feat_file = open(wvcsv,"rb")
    fr = csv.reader(feat_file)
   
    syn_feat = open(syncsv,"rb")
    sr = csv.reader(syn_feat)
        
 
    f = file(csv+".sava", 'wb')
    cPickle.dump((labels,feats), f, protocol=cPickle.HIGHEST_PROTOCOL)
    f.close()    
    


            
def parseXML(im_file):
    """
    extract text from a xml file
    """
    tree = ET.parse(im_file)
    root = tree.getroot()    
    astr = ""
    for txt in root.findall("TEXT"):
        astr += txt.text    
    return astr

def getMSGInfo(astr,axml_file):
    """
    append msgid and sentence id to each sms
    """
    strs = astr.split("\n")
    items = [axml_file]
    for s in strs:
        if re.match("msgid=",s):
            msgid = s.split("=")[1]
            sid = 0
        items.append((msgid,sid,s.strip()))
    return items

def readCorpus(corpus_dir,all_xml_csv):
    parse_csv = open(all_xml_csv,"w")
    pw = csv.writer(parse_csv)
    for (dirpath, dirnames, filenames) in walk(corpus_dir):
        for afile in filenames: 
            if not afile.endswith(".xml"):
                continue
            print afile
            axml_file = os.path.join(dirpath,afile)
            axml_str = parseXML(axml_file)
            axml_info = getMSGInfo(astr,axml_file)
            pw.writerow(axml_info)
    parse_csv.close()

if __name__ == "__main__":
    json_data=open('../../../conf/zeropro.json')
    data = json.load(json_data)
    pprint(data)
    annotation_file = data["annotation_file"]
    gigaword_vector = data["gigaword_vector"]
    corpus = data["corpus"]
    task_dir = data["task_dir"]
    annotation_dict = readCSV(annotation_file)
    task_dict = readTask(task_dir)
#     cmodel = gensim.models.word2vec.Word2Vec.load_word2vec_format(gigaword_vector,binary=True)
#     data["cmodel"] = cmodel
#     data["cmodel"] = "cmodel"
#     readAnnotatedData(annotation_dict,task_dict,**data)
    all_xml_csv = "/home/j/yaqin/Code/SmallPro/data/all_xml_info.csv"
    readCorpus("/home/j/yaqin/Code/SmallPro/data/xml/extract_ouput",all_xml_csv)
    #readSMS(**data)
#     readStagesTrain(**data)
    #writeCSV(annotation_file+".clean",annotation_dict)

    #cmodel = gensim.models.word2vec.Word2Vec.load_word2vec_format(gigaword_vector,binary=True)

    #getWord(cmodel,annotation_dict)
