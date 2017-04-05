import psutil
import time
import os

import Crypto.encryption
from Crypto.liverpoolfs import LiverpoolFS
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

import getpass
import USB.usb

def home(path):
    option = ""
    while option != "c" and option != "u":
        print(option)
        print("A USB device was inserted!\nDo you wish to (c)reate a new key, or (u)se an existing one?")
        option = input()
        if option == "c":
            create(path)
        elif option == "u":
            use(path)
        else:
            print("Invalid option, please try again")

def create(path):
    user = input("Username: ")
    passwd = getpass.getpass()
    keyname = input("Key name: ")
    create_key(path, user, passwd, keyname)

def use(path):
    keys = []
    i = 1
    for key in get_keys(path):
        keyn = Key(os.path.join(path, key))
        keys.append(keyn)
        print(i, ": user:", keyn.username(), "name:", keyn.name())
        i=i+1
    k = input("Select a key:")
    key = keys[int(k)-1].key(getpass.getpass())
    enc = Crypto.Encryption(key)
    def read_callback(cryptext):
        return enc.decrypt(cryptext)
    def write_callback(plaintext):
        return enc.encrypt(plaintext)
    fs = LiverpoolFS("image", read_callback, write_callback)
    pid = os.fork()
    if pid:
        os._exit(0)
    os.setsid()
    pid = os.fork()
    if pid:
        os._exit(0)
    os.close(0)
    os.close(1)
    os.close(2)
    fd = os.open(os.devnull, os.O_RDWR)
    os.dup2(fd, 0)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    FUSE(fs, "mount", foreground=True)


class Key:
    def __init__(self, path):
        self._path = path

    def username(self):
        return os.path.basename(self._path).rsplit("_", 1)[0][4:]

    def name(self):
        return os.path.basename(self._path).rsplit("_", 1)[1]

    def key(self, password):
        handle = open(self._path, "rb")
        encrypted_key = handle.read()
        key_file_decryptor_secret = Crypto.encryption.Encryption.derive_32_byte_key(self.username()+password+self.name())
        key_file_decryptor = Crypto.encryption.Encryption(key_file_decryptor_secret)
        decrypted_key_file = key_file_decryptor.decrypt(encrypted_key)
        handle.close()
        return decrypted_key_file


def get_keys(path):
    for key in filter(lambda x: x.startswith("key_"), os.listdir(path)):
        yield key

def create_key(path, user, password, name):
    key = os.urandom(32)
    key_file_encryptor_secret = Crypto.encryption.Encryption.derive_32_byte_key(user+password+name)
    key_file_encryptor = Crypto.encryption.Encryption(key_file_encryptor_secret)
    encrypted_key = key_file_encryptor.encrypt(key)
    handle = open(os.path.join(path, "key_"+user+"_"+name), "wb+")
    handle.write(encrypted_key)
    handle.close()

def detect():
    olddisks = psutil.disk_partitions()
    found = False
    while not found:
        disks = psutil.disk_partitions()
        for disk in filter(lambda x: x not in olddisks, disks):
            found=True
            home(disk.mountpoint)
            break
        olddisks=disks
        time.sleep(1)

detect()
