import re
import os
import string
import random
import datetime
import time
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'csv', 'doc', 'docx'])

def validUrl(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def validDir(dir):
    dir_len = len(dir)
    re_len = len(re.findall("[a-zA-Z\/]", dir))
    if dir_len == re_len:
        return True
    else:
        return False
        
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def random_file_name(size, ext):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=size)) + '_' + datetime.datetime.fromtimestamp(time.time()).strftime("%d%m%Y%H%M%S")+'.'+ext

def bad_ext_check(ext):
    bad_ext = ['bat', 'exe', 'cmd', 'sh', 'php', 'pl', 'cgi', '386', 'dll', 'com',
            'torrent', 'js', 'app', 'jar', 'pif', 'vb', 'vbscript', 'wsf', 'asp',
            'cer', 'csr', 'jsp', 'drv', 'sys', 'ade', 'adp', 'bas', 'chm', 'cpl', 'crt',
            'csh', 'fxp', 'hlp', 'hta', 'inf', 'ins', 'isp', 'jse', 'htaccess', 'htpasswd',
            'ksh', 'lnk', 'mdb', 'mde', 'mdt', 'mdw', 'msc', 'msi', 'msp', 'mst', 'ops', 'pcd',
            'prg', 'reg', 'scr', 'sct', 'shb', 'shs', 'url', 'vbe', 'vbs', 'wsc', 'wsf', 'wsh',
            'py', 'php', 'php3', 'php4', 'phtml', 'pl', 'htm', 'shtml', 'cgi', 'html']
    if ext is None or ext == '' or ext in bad_ext:
        return False