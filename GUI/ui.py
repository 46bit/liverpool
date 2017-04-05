import getpass
import USB.usb
from Crypto import Encryption

def home(path):
    option = ""
    while option != "c" or option != "u":
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
        keys.add(key)
        print(i, ": user:", key.username, "name:", key.name)
        i=i+1
    k = input("Select a key:")
    key = keys[int(k)-1].key(getpass.getpass())
    enc = Encryption(key)
    def read_callback(cryptext):
        return enc.decrypt(cryptext)
    def write_callback(plaintext):
        return enc.encrypt(plaintext)
    fs = LiverpoolFS("image", read_callback, write_callback)
    FUSE(fs, "mount", nothreads=True, foreground=True, **{'allow_other': True})
