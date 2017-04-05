import nacl.secret
import nacl.utils

class Encryption:

    def __init__(self, key_bytes):
        """ Initialise an encryptor, requires a 32-byte key.
            Raises RuntimeError if key size is invalid. """

        key_size = nacl.secret.SecretBox.KEY_SIZE
        if len(key_bytes) != key_size:
            self.raise_error("Invalid size of encryption key, correct size is " + key_size)

        self.__key_bytes = key_bytes
        self.__secret_box = nacl.secret.SecretBox(self.__key_bytes)


    def encrypt(self, file_bytes):
        """ Encrypt the input file in bytes with the encryptor's
            encryption key, return the output bytes with the nounce
            included.
        """

        if not isinstance(file_bytes, bytes):
            self.raise_error("Data being encrypted is not in bytes.")

        return self.__secret_box.encrypt(file_bytes)


    def decrypt(self, encrypted_bytes):
        """ Decrypt the encrypted file with the encryptor's
            encryption key, return the output bytes of the
            clear text.
        """

        if not isinstance(encrypted_bytes, bytes):
            self.raise_error("Data being decrypted is not in bytes.")

        return self.__secret_box.decrypt(encrypted_bytes)


    @classmethod
    def raise_error(self, error_message):
        """ Utilities function for raising and logging error messages. """

        caller_name = str(sys._getframe(1).f_code.co_name)
        message = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + caller_name + ": " + str(error_message) + "\n"

        try:
            # If we cannot write to the directory or file, not making a fuss.
            log_file = open('crypt.log', 'w+')
            log_file.write(message)
        except:
            pass

        raise RuntimeError(message)
