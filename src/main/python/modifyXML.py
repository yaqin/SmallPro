import os
import sys
import xml.etree.ElementTree as ET


class Extract(object):
    def __init__(self):
        self.xmlfile = []
        self.f_loc = sys.argv[1]
        self.output = sys.argv[1]+"/extract_ouput"
        self.f = os.listdir(self.f_loc)

    def load_data(self):
        for x in self.f:
            if x.endswith('.xml'):
                fname = self.f_loc + x
                self.tree = ET.parse(fname)
                self.root = self.tree.getroot()
                text = self.root[0].text
                dic_start_tag = {}
                for tags in self.root[1]:
                    start = int(tags.attrib["start"])
                    pron = tags.tag
                    dic_start_tag[start] = pron
                dic_start_tag = sorted(dic_start_tag.items(), key=lambda dic: dic[0])
                newtext = text[:dic_start_tag[0][0]] + dic_start_tag[0][1] + "_#"
                for i in range(1, len(dic_start_tag)):
                    newtext = newtext + text[dic_start_tag[i - 1][0] + 5:dic_start_tag[i][0]] + dic_start_tag[i][
                        1] + "_#"
                newtext += text[dic_start_tag[len(dic_start_tag) - 1][0] + 5:]
                self.root[0].text = newtext
                output_name_temp = self.output + "temp" + x
                out_name = self.output + x
                self.tree.write(output_name_temp, "utf-8")

                file_input = open(output_name_temp, 'r')
                file_output = open(out_name, 'w')
                count = 1
                for line in file_input:
                    if line.startswith("suid="):
                        continue
                    elif line.startswith("<TEXT>"):
                        line = line[:len(line) - 1] + "<![CDATA["+"\n"
                        file_output.write(line)
                    elif line.startswith("</TEXT>"):
                        line = "]]>"+line
                        file_output.write(line)
                        file_output.write("</ProTask>")
                        break
                    else:
                        file_output.write(line)
                file_input.close()
                file_output.close()
                os.remove(output_name_temp)

e = Extract()
e.load_data()

