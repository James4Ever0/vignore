<h1 align="center">vignore</h1>

<h2 align="center"><i>Never been so easy to visualize ignore rules</i></h2>

<p align="center">
<a href="https://asciinema.org/a/630043"><img alt="Demo" src="https://asciinema.org/a/630043.svg"></a>
</p>

<p align="center">
<a href="https://github.com/james4ever0/vignore/blob/master/LICENSE"><img alt="License: WTFPL" src="https://img.shields.io/badge/license-UNLICENSE-green.svg?style=flat"></a>
<a href="https://pypi.org/project/vignore/"><img alt="PyPI" src="https://img.shields.io/pypi/v/vignore"></a>
<a href="https://deepwiki.com/James4Ever0/vignore"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
<a href="https://pepy.tech/project/vignore"><img alt="Downloads" src="https://static.pepy.tech/badge/vignore"></a>
<a href="https://github.com/james4ever0/vignore"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

It has been a while since I've found writing ignore files, like `.gitignore`, `.dockerignore`, or `.fdignore`, being a hassle.

I've struggled with including the correct files and excluding unwanted ones.

But now, there's no need to guess blindly! Experience the power of visualizing ignored (selected) files and receive instant feedback through intuitive representations.

**Highlights**
- Asynchronous output, so you can scroll smoothly while processing
- Extremely fast for large repositories
- Human friendly number representations
- Supports `git` and `fd` ignore files
- Supports custom ignore files and custom `fd` arguments (coming soon)

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
