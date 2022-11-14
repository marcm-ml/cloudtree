# ruff: noqa: UP007
from typing import Annotated, Optional
from urllib.parse import urlparse

import fsspec
import typer
from upath import UPath

from cloudtree.cloudtree import SortBy, Stats, TreeDir

app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def cli(
    dir: Annotated[str, typer.Argument(help="Directory to display")],
    depth: Annotated[
        int,
        typer.Option(
            "-d",
            "--depth",
            help="Controls tree depth. 0 means infinite depth. 1 will print only the first directory level, etc.",
        ),
    ] = 0,
    excludes: Annotated[
        Optional[list[str]], typer.Option("-e", "--exclude", help="Exclude files/dirs based on .gitignore syntax.")
    ] = None,
    exclude_regex: Annotated[Optional[str], typer.Option(help="Exclude regex")] = None,
    fs_kwargs: Annotated[
        Optional[list[str]],
        typer.Option(
            "--fs",
            help=(
                "Additional FileSystem Args. Useful for credentials or server-side encryption. "
                "Must be in the form of key=value"
            ),
        ),
    ] = None,
    include_files: Annotated[
        bool, typer.Option("-f/-nf", "--files/--no-files", help="Whether to include also files or only directorys")
    ] = False,
    include_gitignore: Annotated[
        bool,
        typer.Option(
            "--gitignore/--no-gitignore",
            help="Enabled/Disable parsing .gitignore file if present in a directory. "
            "A root-level .gitignore is used everywhere while subdirectory .gitignores "
            "are just valid for children of the subdirectory. "
            "Excludes provided via --excludes will still be respected.",
        ),
    ] = True,
    stats: Annotated[
        Optional[list[Stats]],
        typer.Option(
            "--stat",
            help=(
                "Display statistics. If None (default) no statistics are printed. "
                f"If '{Stats.ALL}' all statistics are printed. You can specify this option multiple times "
                "to included a subset of statistics."
            ),
        ),
    ] = None,
    sort_by: Annotated[
        SortBy, typer.Option("-s", "--sort-by", help="Sort by Name, Creation-Date, Modified-Date, Size or None")
    ] = SortBy.NAME,
    ascending: Annotated[
        bool, typer.Option("-a/-d", "--ascending/--descending", help="Whether to sort in ascending or descending order")
    ] = True,
    color: Annotated[bool, typer.Option("-c/-nc", "--color/--no-color", help="Print with color")] = True,
):
    """
    Cloudtree CLI
    """
    excludes = [] if excludes is None else list(set(excludes))

    # Get filesystem
    scheme = urlparse(dir).scheme
    fs_kwargs = [] if fs_kwargs is None else list(set(fs_kwargs))
    parsed_fs_kwargs = dict(kw.split("=") for kw in fs_kwargs if "=" in kw)
    fs = fsspec.get_filesystem_class(scheme)(**parsed_fs_kwargs)

    # add top level .gitignore for re-use in children
    if include_gitignore and UPath(".gitignore").is_file():
        with UPath(".gitignore").open("r") as f:
            gitignore = f.readlines()
            gitignore.append(".git/")
        excludes = list(set(excludes + gitignore))

    paths = TreeDir.construct_tree(
        root=UPath(dir),
        depth=depth,
        excludes=excludes,
        exclude_regex=exclude_regex or "!.*",
        fs=fs,
        include_files=include_files,
        include_gitignore=include_gitignore,
        color=color,
        sort_by=sort_by,
        ascending=ascending,
    )

    stats = list(set(stats)) if stats else []
    if Stats.ALL in stats:
        stats = list(Stats)
    for _dir in paths:
        print(_dir.format_tree(stats=stats))


def main():
    """Entrypoint"""
    app()


if __name__ == "__main__":
    main()
