#encoding:utf-8
import struct  
import sys,os,shutil

_SignID = 849586
_EncryptKey = "0245897620dkl"

#根目录
ROOTPATH = os.path.dirname(sys.argv[0])
#资源目录
RES_PATH = os.path.join(ROOTPATH,"source","LibHNMutlLobby","res")
#不需要加密的目录
ignoreList = [os.path.join(RES_PATH,"Share"),os.path.join(RES_PATH,"Default")]
#需要加密的文件类型
suffixList = ["png","jpg","jpeg"]

_DELTA = 0x9E3779B9  
  
def _long2str(v, w):  
    n = (len(v) - 1) << 2  
    if w:  
        m = v[-1]  
        if (m < n - 3) or (m > n): return ''  
        n = m  
    s = struct.pack('<%iL' % len(v), *v)  
    return s[0:n] if w else s  
  
def _str2long(s, w):  
    n = len(s)  
    m = (4 - (n & 3) & 3) + n  
    s = s.ljust(m, "\0")  
    v = list(struct.unpack('<%iL' % (m >> 2), s))  
    if w: v.append(n)  
    return v  
  
def encrypt(str, key):  
    if str == '': return str  
    v = _str2long(str, True)  
    k = _str2long(key.ljust(16, "\0"), False)  
    n = len(v) - 1  
    z = v[n]  
    y = v[0]  
    sum = 0  
    q = 6 + 52 // (n + 1)  
    while q > 0:  
        sum = (sum + _DELTA) & 0xffffffff  
        e = sum >> 2 & 3  
        for p in xrange(n):  
            y = v[p + 1]  
            v[p] = (v[p] + ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[p & 3 ^ e] ^ z))) & 0xffffffff  
            z = v[p]  
        y = v[0]  
        v[n] = (v[n] + ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[n & 3 ^ e] ^ z))) & 0xffffffff  
        z = v[n]  
        q -= 1  
    return _long2str(v, False)  
  
def decrypt(str, key):  
    if str == '': return str  
    v = _str2long(str, False)  
    k = _str2long(key.ljust(16, "\0"), False)  
    n = len(v) - 1  
    z = v[n]  
    y = v[0]  
    q = 6 + 52 // (n + 1)  
    sum = (q * _DELTA) & 0xffffffff  
    while (sum != 0):  
        e = sum >> 2 & 3  
        for p in xrange(n, 0, -1):  
            z = v[p - 1]  
            v[p] = (v[p] - ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[p & 3 ^ e] ^ z))) & 0xffffffff  
            y = v[p]  
        z = v[n]  
        v[0] = (v[0] - ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[0 & 3 ^ e] ^ z))) & 0xffffffff  
        y = v[0]  
        sum = (sum - _DELTA) & 0xffffffff  
    return _long2str(v, True)  

def encryptFile(path):
    #读取文件
    src_file = open(path,'rb')
    img_data = src_file.read()
    #获取前4个字节的signid
    sign_id, = struct.unpack("i",img_data[:4])
    src_file.close()
    if sign_id == _SignID :
        print path[len(RES_PATH):] + " encrypt fail, already encrypted"
    else:
        img_data = encrypt(img_data, _EncryptKey)
        des_file = open(path,'wb+')
        pre_sign = struct.pack("i",_SignID)
        des_file.write(pre_sign)
        des_file.write(img_data)
        des_file.close()
        print path[len(RES_PATH):] + " encrypt success"

def decryptFile(path):
    #读取文件
    src_file = open(path,'rb')
    img_data = src_file.read()
    #获取前4个字节的signid
    sign_id, = struct.unpack("i",img_data[:4])
    src_file.close()
    if sign_id == _SignID :
        img_data = decrypt(img_data[4:], _EncryptKey)
        des_file = open(path,'wb')
        des_file.write(img_data)
        des_file.close()
        print path[len(RES_PATH):] + " decrypt success"
    else:
        print path[len(RES_PATH):] + " decrypt fail, not encrypt"

def luaEncrypt(dirpath,backpath):
    src = os.path.join(dirpath,"src")
    res = os.path.join(dirpath,"res")
    if os.path.exists(src) and os.path.exists(res) :
        #先解密
        luaDecrypt(dirpath,backpath)
        #备份src
        newsrc = os.path.join(backpath,os.path.basename(dirpath),"src")
        shutil.move(src,newsrc)
        #加密
        COCOSORDER = "cocos luacompile -s {}/ -d {}/ -e True -k 8sd34kk34nk45kn34A3OssdSO0 -b www.dkl888.com --disable-compile True".format(
                newsrc,
                src
            )
        os.system(COCOSORDER)

def luaDecrypt(dirpath,backpath):
    src = os.path.join(dirpath,"src")
    newsrc = os.path.join(backpath,os.path.basename(dirpath),"src")
    if os.path.exists(src) and os.path.exists(newsrc):
        #删除加密
        shutil.rmtree(src,True)
        #还原
        shutil.move(newsrc,src)

def exit():
    raw_input("press enter to close")
    sys.exit()

if __name__ == "__main__":
    if len(sys.argv) == 2 :
        mode = sys.argv[1]
    else :
        mode = raw_input("encrypt/decrypt (y/n) :")

    if mode != "y" and mode != "n":
        print "param error"
        exit()
        
    #############################
    #加密资源
    #############################
    count = 0
    #三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
    for parent,dirnames,filenames in os.walk(RES_PATH) :
        for filename in filenames :
            path = os.path.join(parent,filename) #完整文件路径
            extension = os.path.splitext(path)[1][1:]

            #忽略不支持的文件类型
            if extension not in suffixList :
                continue

            #忽略指定目录
            isIgnore = False
            for ignore in ignoreList :
                if ignore in path :
                    isIgnore = True
                    break

            if isIgnore :
                continue

            if mode == "y":
                encryptFile(path)
                count = count + 1
            else:
                decryptFile(path)
                count = count + 1

    print "all done! " + str(count) + " files processed"

    #############################
    #加密lua游戏
    #############################
    #lua游戏路径
    luagames = os.path.join(RES_PATH,"Games");
    #备份路径
    gamesbackpath = os.path.join(os.path.dirname(RES_PATH),".luagames")
    for dirname in os.listdir(luagames) :
        path = os.path.join(luagames,dirname)
        if os.path.isdir(path):
            if mode == "y":
                print "lua encrypt " + path
                luaEncrypt(path,gamesbackpath)
            else:
                print "lua decrypt " + path
                luaDecrypt(path,gamesbackpath)

    #############################
    #加密lua框架
    #############################
    luaframework = os.path.join(RES_PATH,"luaplatform");
    framebackpath = os.path.join(os.path.dirname(RES_PATH),".luaplatform")
    if mode == "y":
        print "lua encrypt " + luaframework
        luaEncrypt(luaframework,framebackpath)
    else:
        print "lua decrypt " + luaframework
        #newpath = os.path.join(os.path.dirname(RES_PATH),".luagames");
        #shutil.rmtree(newpath,True)
        luaDecrypt(luaframework,framebackpath)

    ###############################
    #加密lua收尾
    ###############################
    if mode == "n":
        shutil.rmtree(gamesbackpath,True)
        shutil.rmtree(framebackpath,True)
    









