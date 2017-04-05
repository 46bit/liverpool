#!/usr/bin/env python

from __future__ import with_statement

import psutil
import time
import os

import nacl.secret
import nacl.utils
import nacl.hash
import nacl.encoding

import sys
import base64
from time import gmtime, strftime

class Encryption:

    def __init__(self, key_bytes):
        """ Initialise an encryptor, requires a 32-byte key.
            Raises RuntimeError if key size is invalid. """

        key_size = nacl.secret.SecretBox.KEY_SIZE
        if len(key_bytes) != key_size:
            self.raise_error("Invalid size of encryption key, correct size is " + str(key_size))

        self.__key_bytes = key_bytes
        self.__secret_box = nacl.secret.SecretBox(self.__key_bytes)


    def encrypt(self, file_bytes):
        """ Encrypt the input file in bytes with the encryptor's
            encryption key, return the output bytes with the nounce
            included.
        """

        if not isinstance(file_bytes, bytes):
            self.raise_error("Data being encrypted is not in bytes.")
        file_b64 = base64.b64encode(file_bytes)

        return self.__secret_box.encrypt(file_b64, encoder=nacl.encoding.Base64Encoder)


    def decrypt(self, encrypted_bytes):
        """ Decrypt the encrypted file with the encryptor's
            encryption key, return the output bytes of the
            clear text.
        """

        if not isinstance(encrypted_bytes, bytes):
            self.raise_error("Data being decrypted is not in bytes.")

        file_b64 = self.__secret_box.decrypt(encrypted_bytes, encoder=nacl.encoding.Base64Encoder)

        return base64.b64decode(file_b64)


    @staticmethod
    def derive_32_byte_key(source_key):
        """ Given any str or bytes, derive a 32-byte key by
            first hashing with SHA256 and then take first half
            of hash string. This is deterministic.
        """

        # Accept both strings and bytes
        if isinstance(source_key, str):
            source_key = str.encode(source_key)

        if not isinstance(source_key, bytes):
            self.raise_error("Input key is not in bytes or string.")

        hashed_key = nacl.hash.sha256(source_key, encoder=nacl.encoding.HexEncoder)
        derived_key = hashed_key[:nacl.secret.SecretBox.KEY_SIZE]

        return derived_key


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
        key_file_decryptor_secret = Encryption.derive_32_byte_key(self.username()+password+self.name())
        key_file_decryptor = Encryption(key_file_decryptor_secret)
        decrypted_key_file = key_file_decryptor.decrypt(encrypted_key)
        handle.close()
        return decrypted_key_file


def get_keys(path):
    for key in filter(lambda x: x.startswith("key_"), os.listdir(path)):
        yield key

def create_key(path, user, password, name):
    key = os.urandom(32)
    key_file_encryptor_secret = Encryption.derive_32_byte_key(user+password+name)
    key_file_encryptor = Encryption(key_file_encryptor_secret)
    encrypted_key = key_file_encryptor.encrypt(key)
    handle = open(os.path.join(path, "key_"+user+"_"+name), "wb+")
    handle.write(encrypted_key)
    handle.close()

def detect():
    olddisks = psutil.disk_partitions()
    while True:
        disks = psutil.disk_partitions()
        for disk in filter(lambda x: x not in olddisks, disks):
            print(disk.mountpoint)
        olddisks=disks
        time.sleep(1)

import os
import sys
import errno
from collections import defaultdict

from fuse import FUSE, FuseOSError, Operations, fuse_get_context

# An encrypted FUSE filesystem.
#
# This mounts a root directory as a new filesystem. Files on disk are encrypted, then
# this filesystem allows read/writing plaintext files.
#
# Based upon a basic FUSE example, https://github.com/skorokithakis/python-fuse-sample
class LiverpoolFS(Operations):
    def __init__(self, root, read_callback=None, write_callback=None):
        self.root = root
        self.fd_counter = 0
        self.fd_to_full_path = {}
        self.full_path_to_fd = {}
        self.read_callback = read_callback
        self.write_callback = write_callback

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        attrs = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        if os.path.isfile(full_path):
            fh = self.open(path, 'rb')
            plaintext = self._read_plaintext(fh)
            attrs['st_size'] = len(plaintext)
        return attrs

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def _read_plaintext(self, fh):
        full_path = self.fd_to_full_path[fh]
        with open(full_path, 'rb') as f:
            cryptext = f.read().rstrip(b'\0')

        if self.read_callback:
            plaintext = self.read_callback(cryptext)
        else:
            plaintext = cryptext

        return plaintext#.rstrip(b'\0')

    def _write_plaintext(self, fh, plaintext):
        plaintext = plaintext
        if self.write_callback:
            cryptext = self.write_callback(plaintext)
        else:
            cryptext = plaintext

        full_path = self.fd_to_full_path[fh]
        with open(full_path, 'w+b') as f:
            f.write(cryptext.rstrip(b'\0'))

    def open(self, path, flags):
        full_path = self._full_path(path)
        if full_path not in self.full_path_to_fd:
            fd = self.fd_counter + 1
            self.fd_counter += 1
            self.fd_to_full_path[fd] = full_path
            self.full_path_to_fd[full_path] = fd

        fd = self.full_path_to_fd[full_path]
        return fd

    def create(self, path, mode, fi=None):
        uid, gid, pid = fuse_get_context()
        full_path = self._full_path(path)
        fd = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        os.chown(full_path,uid,gid) #chown to context uid & gid
        fd = self.open(path, 'r+b')
        self._write_plaintext(fd, b'')
        return fd

    def read(self, path, length, offset, fh):
        print('READ    ', path, fh, length, offset)
        plaintext = self._read_plaintext(fh)
        plaintext = plaintext[offset:offset + length].rstrip(b'\0')
        print(plaintext)
        return plaintext

    def write(self, path, buf, offset, fh):
        print('WRITE    ', path, fh, offset, buf)
        plaintext = self._read_plaintext(fh)
        plaintext = plaintext[:offset] + buf + plaintext[offset + len(buf):]
        self._write_plaintext(fh, plaintext)
        return len(buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        fh = self.full_path_to_fd[full_path]
        plaintext = self._read_plaintext(fh)
        plaintext = plaintext[:length]
        self._write_plaintext(fh, plaintext)

    def flush(self, path, fh):
        return 0

    def release(self, path, fh):
        self.flush(path, fh)
        return 0

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)

import nacl.secret

user = "46bit"
password = "password"
keyname = "key1"

create_key(".", user, password, keyname)
key = Key("key_%s_%s" % (user, keyname))
enc = Encryption(key.key(password))
def read_callback(cryptext):
    return enc.decrypt(cryptext)
def write_callback(plaintext):
    return enc.encrypt(plaintext)
fs = LiverpoolFS("image", read_callback, write_callback)
FUSE(fs, "mount", nothreads=True, foreground=True, **{'allow_other': True})
