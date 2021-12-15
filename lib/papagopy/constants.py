codes = {
  "all": [
    "ko",       # Korean
    "ja",       # Japanese
    "zh-CN",    # Simplified Chinese
    "zh-TW",    # Traditional Chinese
    "hi",       # Hindi
    "en",       # English
    "es",       # Spanish
    "fr",       # French
    "de",       # German
    "pt",       # Portuguese
    "vi",       # Vietnamese
    "id",       # Indonesian
    "th",       # Thai
    "ru",       # Russian
    "it",       # Italian
  ],
  "n2mt": [
    'ko', 'en', 'ja', 'zh-CN', 'zh-TW',
    'vi', 'id', 'th', 'de', 'ru', 
    'es', 'it', 'fr',
  ],
  "nsmt": [
    'hi', 'pt',
  ],
  "n2mtAPI": {
    'ko': [
      'en', 'ja', 'zh-CN', 'zh-TW', 'vi',
      'id', 'th', 'de', 'ru', 'es',
      'it', 'fr',
    ],
    'ja': ['ko', 'en', 'zh-CN', 'zh-TW', ],
    'zh-CN': ['ko', 'en', 'ja', 'zh-TW', ],
    'zh-TW': ['ko', 'en', 'ja', 'zh-CN', ],
    'hi': [],
    'en': ['ko', 'ja', 'fr', 'zh-CN', 'zh-TW', ],
    'es': ['ko', ],
    'fr': ['ko', ],
    'de': ['ko', ],
    'pt': [],
    'vi': ['ko', ],
    'id': ['ko', ],
    'th': ['ko', ],
    'ru': ['ko', ],
    'it': ['ko', ],
  }
}

url = {
  "main": "https://papago.naver.com",
  "api": {
    "dect": 'https://openapi.naver.com/v1/papago/detectLangs',
    "n2mt": 'https://openapi.naver.com/v1/papago/n2mt',
  },
  "web": {
    "dect": 'https://papago.naver.com/apis/langs/dect',
    "nsmt": 'https://papago.naver.com/apis/nsmt/translate',
    "n2mt": 'https://papago.naver.com/apis/n2mt/translate',
    "tts": 'https://papago.naver.com/apis/tts/makeID',
  }
}


tts = {
  "male": {
    "ko": "jinho",
    "ja": "shinji",
    "zh-CN": "liangliang",
    "zh-TW": "kuanlin",
    "hi": "",
    "en": "matt",
    "es": "jose",
    "fr": "louis",
    "de": "tim",
    "pt": "",
    "vi": "",
    "id": "",
    "th": "sarawut",
    "ru": "aleksei",
    "it": "",
  },
  "female": {
    "ko": "kyuri",
    "ja": "yuri",
    "zh-CN": "meimei",
    "zh-TW": "chiahua",
    "hi": "",
    "en": "clara",
    "es": "carmen",
    "fr": "roxane",
    "de": "lena",
    "pt": "",
    "vi": "",
    "id": "",
    "th": "somsi",
    "ru": "vera",
    "it": "",
  },
  "speed": { # -5 to 5
    "verySlow": 5,    # very slow
    "slow": 3,    # slow
    "normal": 0,    # normal
    "fast": -1,   # fast
  }
}


testString = {
  "ko": '다양한 네이버 서비스를 즐겨보세요.',
  'ja': '考え過ぎないでください',
  'zh-CN': '今年只是在越南有两个活动安排',
  'zh-TW': '我再也不願意給克莉絲蒂娜當副手了——我要另找一份工作！',
  'hi': 'मैं खाना खाता हूँ।',
  'en': 'The key word here is "update"',
  'es': '¿Dónde estás ahora mismo?',
  'fr': 'Lundi, la lune était très belle ! ',
  'de': 'Das Buch ist sehr gut, da es sehr witzig ist.',
  'pt': 'simpatia com ele inclinou no coração.',
  'vi': 'có bao nhiều quả táo?',
  'id': 'karam sambal oléh belacan',
  'th': 'บีทีเอส ใกล้ ที่สุด อยู่ที่ไหน ค่ะ',
  'ru': 'я часто гулял на парке.',
  'it': 'A che ora ci incontriamo?',
}
