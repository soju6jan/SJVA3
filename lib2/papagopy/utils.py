import shutil
import requests

from . import constants as CONST

def languages():
  print(f'Supported language codes: {", ".join(CONST.codes["all"])}')

def makePrintableString(source, SIZE=30):
  MAX = SIZE
  if type(source) != type(''):
    source = str(source)
  length = len(source)
  if length <= MAX*2:
    return source
  else:
    quater = int(length/3)
    size = MAX if quater > MAX else quater
    return (source[:size] + '...' + source[-size:]).strip()

def canTranslateDirectly(sourceCode, targetCode):
  return not (
    (sourceCode in CONST.codes['nsmt'] and targetCode != 'en') or \
    (targetCode in CONST.codes['nsmt'] and sourceCode != 'en')
  )

def useNSMT(sourceCode, targetCode):
  return (sourceCode in CONST.codes['nsmt']) or (targetCode in CONST.codes['nsmt'])

def splitLongText(source, size=4501, forLangDetection=False, debug=False):
  delimiter = ['。', '？', '！', '.', '?', '!', '\n', ]
  delimiter_2nd = [',', ':', ')', ']', '}', '>', '~', ';', '】', '、', '，', '…', '‥', '」', '』', '〟', '⟩', ]
  delimiter_last = [' ']
  MAXSIZE = size

  sourceText = source
  result = []

  # add space to japanese punctuation marks
  replace_dict = {'。': '。 ', '、': '、 ', '，': '， '}
  sourceText.maketrans(replace_dict)

  while True:
    index = MAXSIZE

    if forLangDetection and len(result) > 4:
      break

    if index > len(sourceText):
      result.append(sourceText)
      break

    while sourceText[index] not in delimiter and index > 0:
      index -= 1
    
    if debug:
      if sourceText[index] == '\n':
        print('[Papago.splitLongText] first check delimiter end. index: '+str(index)+'. character: "\\n."')
      else:
        print('[Papago.splitLongText] first check delimiter end. index: '+str(index)+'. character: "'+sourceText[index])


    if index <= 0:
      index = MAXSIZE
      while sourceText[index] not in delimiter_2nd and index > 0:
        index -= 1  
      if debug:
        print('[Papago.splitLongText] second check delimiter end. index: '+str(index)+'. character: "'+sourceText[index])
    
    if index <= 0:
      index = MAXSIZE
      while sourceText[index] not in delimiter_last and index > 0:
        index -= 1
      if debug:
        print('[Papago.splitLongText] last check delimiter end. index: '+str(index)+'. character: "'+sourceText[index])
    
    if index <= 0:
      index = MAXSIZE

    result.append(sourceText[:index+1])
    sourceText = sourceText[index+1:]

  if debug:
    print('[Papago.splitLongText] original text length '+str(len(source))+' splitted to '+str(len(result))+' chunks.')
    for t in result:
      print('[Papago.splitLongText] splitted text length '+str(len(t))+' - '+makePrintableString(t))
  return result

def isValidCode(code):
  return (code in CONST.codes['all'])

def isAPIusable(sourceCode, targetCode):
  return (targetCode in CONST.codes['n2mtAPI'][sourceCode])

def downloadAudio(url, filename=''):
  if len(filename) < 1:
    filename = f"{url.split('/')[-1]}.mp3"
  if not (filename.endswith('.mp3') or filename.endswith('.wav')):
    filename += '.mp3'
  with requests.get(url, stream=True) as stream:
    with open(filename, 'ab') as f:
      shutil.copyfileobj(stream.raw, f)
  return filename