import math
import re
from collections.abc import Generator, Iterable, Iterator
from enum import Enum
from typing import TypeVar

import fsspec
import pathspec
from termcolor import colored
from upath import UPath


class Stats(str, Enum):
    """Stats Enum"""

    SIZE = "size"
    CREATION_DATE = "creation"
    LAST_MODIFIED = "modified"
    ALL = "all"

    def stat(self, path: UPath):
        """Return string"""
        try:
            if self.value == Stats.SIZE:
                return f"Size: {convert_size(path.fs.size(path))}"
            elif self.value == Stats.CREATION_DATE:
                return f"Created at: {path.fs.created(path)}"
            elif self.value == Stats.LAST_MODIFIED:
                return f"Modified at: {path.fs.modified(path)}"
            elif self.value == Stats.ALL:
                return ""
            else:
                raise NotImplementedError("")
        except Exception:
            return ""


class SortBy(str, Enum):
    """Sort by Enum"""

    NONE = "none"
    NAME = "name"
    SIZE = "size"
    CREATION_DATE = "creation"
    LAST_MODIFIED = "modified"


class TreeDir:
    """
    Extracts a tree structure recursively.

    Construct tree using ``TreeDir.construct_tree()``. Returns a list of TreeDir
    instances which can be turned into printable strings by using class method
    ``tree_dir_instance.format_tree()``

    Example:
        paths = DisplayablePath.make_tree(".")
        for path in paths:
            print(path.format_tree())

    Adapted from
    https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
    """

    prefix_middle = "├──"
    prefix_last = "└──"
    prefix_middle_parent = "    "
    prefix_last_parent = "│   "

    def __init__(
        self,
        path: UPath,
        is_last: bool,
        fs: fsspec.AbstractFileSystem,
        parent_path: "TreeDir | None" = None,
        color: bool = True,
    ):
        """
        Constructs TreeDir object which represents a path to dir or file inside a
        """
        self.path = path
        self.parent = parent_path
        self.is_last = is_last
        if self.parent is not None:
            self.depth = self.parent.depth + 1  # type: int
        else:
            self.depth = 0
        self.fs = fs
        self.color: bool = color

    @property
    def displayname(self) -> str:
        """
        Displays name of dir/file
        """
        name = self.path.name
        if self.path.is_dir():
            name += "/"
            if self.color:
                name = colored(name, color="light_blue")
        return name

    @classmethod
    def construct_tree(
        cls,
        root: UPath,
        depth: int,
        excludes: list[str],
        exclude_regex: str,
        fs: fsspec.AbstractFileSystem,
        include_files: bool,
        include_gitignore: bool,
        color: bool,
        sort_by: SortBy,
        ascending: bool = True,
        is_last: bool = False,
        parent: "TreeDir | None" = None,
    ) -> Generator["TreeDir", None, None]:
        """
        Constructs Tree recursively
        """
        # add root-level ignore
        local_excludes = []
        if parent is not None and include_gitignore and (root / ".gitignore").is_file():
            with (root / ".gitignore").open("r") as f:
                local_excludes = list(set(f.readlines()))

        filterspec = pathspec.GitIgnoreSpec.from_lines(set(excludes + local_excludes))

        # Get protocol for FileSystem
        root = root.resolve()

        # Yield root
        displayable_root = cls(path=root, parent_path=parent, is_last=is_last, fs=fs, color=color)
        yield displayable_root

        # max depth reached?
        if 0 < depth <= displayable_root.depth:
            return

        # WARNING: this can be very costly operation!
        # Get children based on filter and sort alphabetically
        # create chained generators that are evaluated at the last step to avoid unecessary iterations
        _children = (
            path
            for path in set(root.glob("*"))
            if not filterspec.match_file(path.name + path.anchor)
            and not re.match(exclude_regex, path.name + path.anchor)
        )
        children = sort_files_dirs(paths=_children, include_files=include_files, sort_by=sort_by, ascending=ascending)

        for path, is_last in last_iteration(children):
            if path.is_dir():
                yield from cls.construct_tree(
                    root=path,
                    fs=fs,
                    excludes=excludes,
                    exclude_regex=exclude_regex,
                    include_gitignore=include_gitignore,
                    include_files=include_files,
                    is_last=is_last,
                    depth=depth,
                    parent=displayable_root,
                    color=color,
                    sort_by=sort_by,
                    ascending=ascending,
                )
            else:
                yield cls(path=path, parent_path=displayable_root, is_last=is_last, fs=fs, color=color)

    def format_tree(self, stats: Iterable[Stats]) -> str:
        """
        Constructs string which represent the file given the tree structure

        Returns:
            str: String
        """

        # Is path at root?
        if self.parent is None:
            return colored(str(self.path), "magenta") if self.color else str(self.path)

        # Construct prefix for filepath
        _filename_prefix = self.prefix_last if self.is_last else self.prefix_middle

        # Get string parts including prefix for filepath
        part = f"{_filename_prefix} {self.displayname}"
        if self.path.is_file():
            stats_str = " | ".join(stat.stat(self.path) for stat in stats if stat.stat(self.path))
            if stats_str:
                part = part + f" ({stats_str})"

        parts = [part]

        # Add prefixes for all parents (depth level)
        parent = self.parent
        while parent and parent.parent is not None:
            parts.append(self.prefix_middle_parent if parent.is_last else self.prefix_last_parent)
            parent = parent.parent

        return "".join(reversed(parts))


def convert_size(size_bytes: int):
    """
    Convers file size in bytes to appropaite size foramt

    Adapted from

    https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    if i == 0:
        s = int(s)
    return f"{s} {size_name[i]}"


def sort_files_dirs(paths: Iterable[UPath], include_files: bool, sort_by: SortBy, ascending: bool) -> list[UPath]:
    """Sort directory and files alphabetically in set paths and return directory first and then files"""

    def sort_name(path: UPath):
        return str(path.name).lower()

    def sort_size(path: UPath):
        return path.fs.size(path)

    def sort_created(path: UPath):
        try:
            return path.fs.created(path)
        except Exception:
            return sort_name(path)

    def sort_modified(path: UPath):
        try:
            return path.fs.modified(path)
        except Exception:
            return sort_name(path)

    dirs = []
    files = []
    for path in paths:
        if path.is_dir():
            dirs.append(path)
        elif include_files:
            files.append(path)

    # need to negate ascending because list is reverted later
    if sort_by == SortBy.NAME:
        sorted_paths = sorted(dirs, key=sort_name, reverse=not ascending) + sorted(
            files, key=sort_name, reverse=not ascending
        )
    elif sort_by == SortBy.SIZE:
        sorted_paths = sorted(dirs, key=sort_name, reverse=not ascending) + sorted(
            files, key=sort_size, reverse=not ascending
        )
    elif sort_by == SortBy.CREATION_DATE:
        sorted_paths = sorted(dirs, key=sort_created, reverse=not ascending) + sorted(
            files, key=sort_created, reverse=not ascending
        )
    elif sort_by == SortBy.LAST_MODIFIED:
        sorted_paths = sorted(dirs, key=sort_modified, reverse=not ascending) + sorted(
            files, key=sort_modified, reverse=not ascending
        )
    else:
        sorted_paths = dirs + files
    return sorted_paths


T = TypeVar("T")


def last_iteration(iterable: Iterable[T]) -> Iterator[tuple[T, bool]]:
    """Handle last element specially"""
    it = iter(iterable)
    try:
        prev = next(it)
    except StopIteration:
        return  # if the iterable is empty

    for item in it:
        yield prev, False
        prev = item

    yield prev, True  # last element
