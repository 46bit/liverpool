import psutil
import time
import os
import GUI.ui

import Crypto.encryption

class Key:
    def __init__(self, path):
        self._path = path

    def username(self):
        return os.path.basename(self._path).rsplit("_", 1)[0][4:]

    def name(self):
        return os.path.basename(self._path).rsplit("_", 1)[1]

    def key(self, password):
        handle = open(self._path, "rb")
        encrypted_key = handle.read().rstrip("\n")
        key_file_decryptor_secret = Crypto.encrytion.derive_32_byte_key(self.username()+password+self.name())
        key_file_decryptor = Crypto.encrytion.Encryption(key_file_decryptor_secret)
        decrypted_key_file = key_file_decryptor.decrypt(encrypted_key)
        handle.close()
        return key


def get_keys(path):
    for key in filter(lambda x: x.startswith("key_"), os.listdir(path)):
        yield key

def create_key(path, user, password, name):
    key = os.urandom(32)
    key_file_encryptor_secret = Crypto.encrytion.derive_32_byte_key(user+password+name)
    key_file_encryptor = Crypto.encrytion.Encryption(key_file_encryptor_secret)
    encrypted_key = key_file_encryptor.encrypt(key)
    handle = open(os.path.join(path, "key_"+user+"_"+name), "wb+")
    handle.write(key)
    handle.close()

def detect():
    olddisks = psutil.disk_partitions()
    while True:
        disks = psutil.disk_partitions()
        for disk in filter(lambda x: x not in olddisks, disks):
            GUI.ui.home(disk.mountpoint)
        olddisks=disks
        time.sleep(1)

detect()
