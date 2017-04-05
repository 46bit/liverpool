# python-fuse-sample

This repo contains a very simple FUSE filesystem example in Python. It's the
code from a post I wrote a while back:

https://www.stavros.io/posts/python-fuse-filesystem/

If you see anything needing improvement or have any feedback, please open an
issue.

## How to start

OSX:

```
pip3 install fusepy
```

Mount the current directory as a FUSE disk at `../ABC`.

``` sh
mkdir ../ABC
sudo python3 passthrough.py . ../ABC
```
