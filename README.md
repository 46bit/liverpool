# LiverpoolFS

Encrypted FUSE filesystem, built at a hackday and not suitable for real-world use.

## Usage

This runs on Python 3.

To install dependencies:
```
pip install -r DEPENDENCIES
```
To run LiverpoolFS:

```
python main.py
```

The encrypted virtual filesystem can be accessed via `mount/`, whose content will be stored encrypted under `image/`. 
