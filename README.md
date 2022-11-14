# CloudTree

Like unix tree command but with remote-storage support by using fsspec.

Similar to [tree](https://wiki.ubuntuusers.de/tree/) CLI on UNIX and MacOS systems.

Supports any filesystem that fsspec supports.

## Installation

### Standard

Requires >= Python3.9

Install with pip from git:

```shell
pip install git+https://github.com/marcm-ml/cloudtree.git
```

or via ssh

```shell
pip install git+ssh://github.com:marcm-ml/cloudtree.git
```

### Add optional dependencies

Install with extras dependencies such as s3fs (AWS S3 support):

```shell
pip install "cloudtree[s3]@git+https://github.com/marcm-ml/cloudtree.git"
```

See [fsspec docs](https://filesystem-spec.readthedocs.io/en/latest/api.html#other-known-implementations) for more informations about supported filesystems.

Afterwards the cli (cloudtree) is available within the python environment you have installed this package.

## Usage

```shell
 Usage: cloudtree [OPTIONS] DIR

 Cloudtree CLI

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    dir      TEXT  Directory to display [default: None] [required]                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --depth               -d                       INTEGER                             Controls tree depth. 0 means infinite depth. 1 will print only the first          │
│                                                                                    directory level, etc.                                                             │
│                                                                                    [default: 0]                                                                      │
│ --exclude             -e                       TEXT                                Exclude files/dirs based on .gitignore syntax. [default: None]                    │
│ --exclude-regex                                TEXT                                Exclude regex [default: None]                                                     │
│ --fs                                           TEXT                                Additional FileSystem Args. Useful for credentials or server-side encryption.     │
│                                                                                    Must be in the form of key=value                                                  │
│                                                                                    [default: None]                                                                   │
│ --files               -f  --no-files      -nf                                      Whether to include also files or only directorys [default: nf]                    │
│ --gitignore               --no-gitignore                                           Enabled/Disable parsing .gitignore file if present in a directory. A root-level   │
│                                                                                    .gitignore is used everywhere while subdirectory .gitignores are just valid for   │
│                                                                                    children of the subdirectory. Excludes provided via --excludes will still be      │
│                                                                                    respected.                                                                        │
│                                                                                    [default: gitignore]                                                              │
│ --stat                                         [size|creation|modified|all]        Display statistics. If None (default) no statistics are printed. If 'all' all     │
│                                                                                    statistics are printed. You can specify this option multiple times to included a  │
│                                                                                    subset of statistics.                                                             │
│                                                                                    [default: None]                                                                   │
│ --sort-by             -s                       [none|name|size|creation|modified]  Sort by Name, Creation-Date, Modified-Date, Size or None [default: name]          │
│ --ascending           -a  --descending    -d                                       Whether to sort in ascending or descending order [default: a]                     │
│ --color               -c  --no-color      -nc                                      Print with color [default: c]                                                     │
│ --install-completion                                                               Install completion for the current shell.                                         │
│ --show-completion                                                                  Show completion for the current shell, to copy it or customize the installation.  │
│ --help                                                                             Show this message and exit.                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Some Examples

### List all files and dirs in current local directory

Prints only dirs

```shell
cloudtree .
```

Include files

```shell
cloudtree . -f
```

### List all files and dirs from different directory

```shell
cloudtree path/to/dir -f
```

### List all dirs in S3 bucket

Make sure to install with extra option "s3" (see [Installation](#installation))
See s3fs S3FileSystem implementations for available kwargs.
Same goes for other implementations that require some kwargs or authentication.
You must provide the `s3://` schema prefix

```shell
cloudtree s3://<bucket-name>  --fs-kwarg profile=MY_AWS_PROFILE  # botocore env vars are also used
```

### Limit tree depth size to 3 and include files

```shell
cloudtree . -d 3 -f
```

### Filter files/dirs which are hidden (dot-files), starting with "__" and/or match "exclude_me"

```shell
cloudtree . --exclude ".*" --exclude "__*" --exclude "exclude_me"
```
