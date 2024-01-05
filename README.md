# vignore

It is been a while that I hate to write ignore files, be it `.gitignore`, `.dockerignore` or `.fdignore`.

I failed to get the right files included, and failed to exclude unwanted files.

No more shooting in the blind! Visualize ignored (selected) files and get instant feedback in intuitive representations.

**Highlights**
- Asynchronous output, so you can scroll smoothly while processing
- Extremely fast for large repositories
- Supports `git` and `fd` ignore files
- Supports custom ignore files and custom `fd` arguments (coming soon)

## Demo

[![asciicast](https://asciinema.org/a/630043.svg)](https://asciinema.org/a/630043)

## Install

```
pip3 install vignore
```

## Usage

The `diffpath` shall be absolute.

```
vignore [-h] -d DIFFPATH

optional arguments:
  -h, --help            show this help message and exit
  -d DIFFPATH, --diffpath DIFFPATH
                        Path to visualize ignored files
```

## Requirements

You need to install [`fd`](https://github.com/sharkdp/fd), a fast `find` alternative.

You need to run this under a Unix-like OS.