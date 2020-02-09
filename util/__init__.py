from datetime import datetime, timedelta
import pytz
from Crypto.Cipher import AES

_EPOCH = datetime(1970, 1, 1, tzinfo=pytz.utc)

def decryptString(strings,
            pad=lambda s : s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING,
            unpad=lambda s : s[:-ord(s[len(s) - 1:])]):
    try:
        strings = strings.replace("~", "=")
        strings = strings.replace("_","/")
        strings = strings.replace("-","+")

        iv = "0ZmtobK/f2z4fZC9" 
        key = "eoqkr!@#2015est=" 
    
        destr = base64.b64decode(strings)
        chiper = AES.new(key, AES.MODE_CBC, IV=iv)
        return unpad(chiper.decrypt(destr)).decode("utf-8")
    except:
        return -1

def format_date(date):
    return date.strftime("%Y-%m-%d")
    

def format_datetime(datetime):
    return datetime.strftime("%Y-%m-%d %H:%M:%S")


def getNowDateTime():
    return format_datetime(datetime.now())        