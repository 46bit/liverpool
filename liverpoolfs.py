#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
from collections import defaultdict

from fuse import FUSE, FuseOSError, Operations, fuse_get_context


class LiverpoolFS(Operations):
    def __init__(self, root, read_callback=None, write_callback=None):
        self.root = root
        self.fd_counter = 0
        self.fd_access_counts = defaultdict(int)
        self.fd_to_full_path = {}
        self.full_path_to_fd = {}
        self.handlers = {}
        self.plaintexts = {}
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
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

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

    def open(self, path, flags):
        full_path = self._full_path(path)
        if full_path not in self.full_path_to_fd:
            fd = self.fd_counter + 1
            self.fd_counter += 1
            self.fd_to_full_path[fd] = full_path
            self.full_path_to_fd[full_path] = fd

            self.handlers[fd] = os.open(full_path, flags)
            # @TODO: Un-hardcode limit to read.
            cryptext = os.read(self.handlers[fd], 100000000)
            if self.read_callback:
                plaintext = self.read_callback(cryptext)
            else:
                plaintext = cryptext
            self.plaintexts[fd] = plaintext
        else:
            fd = self.full_path_to_fd[full_path]
        self.fd_access_counts[fd] += 1
        print('OPEN    ', fd, path, flags, self.fd_access_counts[fd])
        return fd

    def create(self, path, mode, fi=None):
        uid, gid, pid = fuse_get_context()
        full_path = self._full_path(path)
        fd = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
        os.chown(full_path,uid,gid) #chown to context uid & gid
        return fd

    def read(self, path, length, offset, fh):
        end_position = offset + length
        plaintext_length = len(self.plaintexts[fh])
        end_position = min(offset + length, plaintext_length - 1)
        start_position = min(offset, plaintext_length - 1)
        return self.plaintexts[fh][start_position:end_position]

    def write(self, path, buf, offset, fh):
        start_position = offset
        end_position = offset + len(buf)

        plaintext = bytearray(self.plaintexts[fh])
        plaintext[start_position:end_position] = buf
        self.plaintexts[fh] = bytes(plaintext)
        print('WRITE   ', end_position - start_position)
        return end_position - start_position

    def truncate(self, path, length, fh=None):
        print('TRUNCATE   ', path, length)
        fh = self.open(path, 'r+')
        self.plaintexts[fh] = bytes(bytearray(self.plaintexts[fh])[0:length])
        self.release(path, fh)

    def flush(self, path, fh):
        print(path, fh, self.fd_to_full_path)
        plaintext = self.plaintexts[fh]
        if self.write_callback:
            cryptext = self.write_callback(plaintext)
        else:
            cryptext = plaintext
        os.write(self.handlers[fh], cryptext)
        return 0

    def release(self, path, fh):
        print('RELEASE   ', fh, path, self.fd_access_counts[fh])
        self.flush(path, fh)
        if self.fd_access_counts[fh] == 1:
            ret = os.close(self.handlers[fh])
            full_path = self.fd_to_full_path[fh]
            del self.fd_access_counts[fh]
            del self.fd_to_full_path[fh]
            del self.full_path_to_fd[full_path]
            del self.handlers[fh]
            del self.plaintexts[fh]
        else:
            self.fd_access_counts[fh] -= 1
            ret = 0
        return ret

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(mountpoint, root):
    FUSE(LiverpoolFS(root), mountpoint, nothreads=True, foreground=True, **{'allow_other': True})


if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
