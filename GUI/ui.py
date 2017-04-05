import getpass
import USB.usb
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
    key = keys[int(k)-1] 
