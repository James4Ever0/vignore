# vignore

It has been a while since I've found writing ignore files, like .gitignore, .dockerignore, or .fdignore, to be a hassle.

I've struggled with including the correct files and excluding unwanted ones.

But now, there's no need to guess blindly! Experience the power of visualizing ignored (selected) files and receive instant feedback through intuitive representations.

**Highlights**
- Asynchronous output, so you can scroll smoothly while processing
- Extremely fast for large repositories
- Human friendly number representations
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