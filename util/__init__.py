from datetime import datetime, timedelta
import pytz
from tzlocal import get_localzone
from Crypto.Cipher import AES

_EPOCH = datetime(1970, 1, 1, tzinfo=pytz.utc)


def decryptString(strings,
                  pad=lambda s: s + (BLOCK_SIZE - len(s) %
                                     BLOCK_SIZE) * PADDING,
                  unpad=lambda s: s[:-ord(s[len(s) - 1:])]):
    try:
        strings = strings.replace("~", "=")
        strings = strings.replace("_", "/")
        strings = strings.replace("-", "+")

        iv = "0ZmtobK/f2z4fZC9"
        key = "eoqkr!@#2015est="

        destr = base64.b64decode(strings)
        chiper = AES.new(key, AES.MODE_CBC, IV=iv)
        return unpad(chiper.decrypt(destr)).decode("utf-8")
    except:
        return -1


def dateFormatting(date):
    return date.strftime("%Y-%m-%d")


def datetimeFormatting(datetime):
    return datetime.strftime("%Y-%m-%d %H:%M:%S")


def parseDatetime(text):
    try:
        dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    return get_localzone().localize(dt)


def getNowDateTime():
    return datetimeFormatting(datetime.now())


def getBeforeDaytime():
    text = datetimeFormatting(datetime.now() - timedelta(days=1))
    try:
        date = str(parseDatetime(text).year)
        dateTemp = str(parseDatetime(text).month)
        date += dateTemp.zfill(2)
        dateTemp2 = str(parseDatetime(text).day)
        date += dateTemp2.zfill(2)

    except ValueError:
        date = str(datetime.strptime(text, "%Y-%m-%d").year)
        date += str(datetime.strptime(text, "%Y-%m-%d").month)
        date += str(datetime.strptime(text, "%Y-%m-%d").day)

    return int(date)
