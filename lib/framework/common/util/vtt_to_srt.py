# -*- coding: utf-8 -*-
#########################################################
import re

def convert_vtt_to_srt(fileContents):
    data = _step1(fileContents).strip()
    regex = re.compile(r'\d{2}:\d{2}(:\d{2})?(,\d{3})?\s-->\s\d{2}:\d{2}(:\d{2})?(,\d{3})?')
    ret = []
    idx = 1
    pre_line = None
    for tmp in data.split('\n'):
        match = regex.match(tmp)
        if match:
            #if pre_line is not None and pre_line != str(idx):
            if pre_line != str(idx):
                ret.append(str(idx))
            idx += 1
        ret.append(tmp.strip())
        pre_line = tmp.strip()
    data = '\n'.join(ret).strip()
    data = data.replace('&nbsp;', ' ')
    return data
        



    
def _step1(fileContents):
    fileContents = fileContents.replace('\r\n', '\n')
    replacement = re.sub(r'(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', fileContents)
    replacement = re.sub(r'(\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', replacement)
    replacement = re.sub(r'(\d\d).(\d\d\d) --> (\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', replacement)
    replacement = re.sub(r'WEBVTT(.*?)?\n', '', replacement)
    replacement = re.sub(r'Kind:[ \-\w]+\n', '', replacement)
    replacement = re.sub(r'Language:[ \-\w]+\n', '', replacement)
    #replacement = re.sub(r'^\d+\n', '', replacement)
    #replacement = re.sub(r'\n\d+\n', '\n', replacement)
    replacement = re.sub(r'<c[.\w\d]*>', '', replacement)
    replacement = re.sub(r'</c>', '', replacement)
    replacement = re.sub(r'<\d\d:\d\d:\d\d.\d\d\d>', '', replacement)
    replacement = re.sub(r'::[\-\w]+\([\-.\w\d]+\)[ ]*{[.,:;\(\) \-\w\d]+\n }\n', '', replacement)
    replacement = re.sub(r'Style:\n##\n', '', replacement)
    return replacement

def convert_srt_to_vtt(fileContents):
    vtt_data = 'WEBVTT\n\n'
    for line in fileContents.splitlines():
        convline = re.sub(',(?! )', '.', line)
        vtt_data = vtt_data + convline + '\n'
    return vtt_data
