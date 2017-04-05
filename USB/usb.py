import psutil
import time
import os

class Key:
    def __init__(self, path):
        self._path = path

    def username(self):
        return os.path.basename(self._path).rsplit("_", 1)[0][4:]

    def name(self):
        return os.path.basename(self._path).rsplit("_", 1)[1]

    def key(self):
        handle = open(self._path, "rb")
        key = handle.read().rstrip("\n")
        handle.close()
        return key


def get_keys(path):
    for key in filter(lambda x: x.startswith("key_"), os.listdir(path)):
        yield key

def create_key(path, user, name):
    key = os.urandom(32)
    handle = open(os.path.join(path, "key_"+user+"_"+name), "wb+")
    handle.write(key)
    handle.close()

def detect():
    olddisks = psutil.disk_partitions()
    while True:
        disks = psutil.disk_partitions()
        for disk in filter(lambda x: x not in olddisks, disks):
            print(disk.mountpoint)
        olddisks=disks
        time.sleep(1)
