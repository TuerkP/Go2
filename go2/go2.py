import argparse
import os
import json
import sys
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence, Tuple, cast
from dataclasses import dataclass


class BookmarkError(Exception):
    pass


@dataclass
class CommandInfo:
    cmd: str
    description: str
    arguments: Tuple[str, ...]
    callback: Callable[..., None]


CFG_FILE_PATH = Path(__file__).parent / 'go2.cfg'
COMMANDS: Dict[str, CommandInfo] = {}


def Command(
    name: str, description: str, *arguments: str
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    def Decorator(func: Callable[..., None]) -> Callable[..., None]:
        COMMANDS[name] = CommandInfo(name, description, arguments, func)
        return func
    return Decorator


def LoadBookmarkConfig() -> Dict[str, str]:
    if not CFG_FILE_PATH.exists():
        WriteBookmarkConfig({})

    try:
        with open(CFG_FILE_PATH, 'r', encoding='utf-8') as file:
            rawConfig: object = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise BookmarkError(
            f'Invalid configuration "{CFG_FILE_PATH}": {error}'
        ) from error

    invalidConfig = (
        f'Invalid configuration "{CFG_FILE_PATH}": '
        'expected a JSON object mapping bookmark names to directory paths'
    )
    if not isinstance(rawConfig, dict):
        raise BookmarkError(invalidConfig)

    config: Dict[str, str] = {}
    for bookmark, targetPath in cast(Dict[object, object], rawConfig).items():
        if not isinstance(bookmark, str) or not isinstance(targetPath, str):
            raise BookmarkError(invalidConfig)
        config[bookmark] = targetPath
    return config


def WriteBookmarkConfig(config: Dict[str, str]) -> None:
    with open(CFG_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=2)


def ResolveDirectory(targetPath: str) -> Path:
    target = Path(targetPath).resolve()
    if not target.is_dir():
        raise BookmarkError(f'"{targetPath}" is not a valid directory')
    return target


def GetBookmarkPath(config: Dict[str, str], bookmark: str) -> Path:
    if bookmark not in config:
        raise BookmarkError(f'Unknown bookmark: {bookmark}')
    return ResolveDirectory(config[bookmark])


@Command('add', 'Adds a new bookmark', 'bookmark', 'target')
def CmdAddBookmark(bookmark: str, targetPath: str) -> None:
    if bookmark in COMMANDS or bookmark.startswith('-'):
        raise BookmarkError(f'Bookmark name "{bookmark}" is reserved')

    target = ResolveDirectory(targetPath)
    paths = LoadBookmarkConfig()
    paths[bookmark] = str(target)
    WriteBookmarkConfig(paths)


@Command('del', 'Deletes a bookmark', 'bookmark')
def CmdDelBookmark(bookmark: str) -> None:
    paths = LoadBookmarkConfig()
    paths.pop(bookmark, None)
    WriteBookmarkConfig(paths)


@Command('cfg', 'Opens the go2 configuration file')
def CmdOpenCfg() -> None:
    if not CFG_FILE_PATH.exists():
        WriteBookmarkConfig({})
    os.startfile(str(CFG_FILE_PATH))


@Command('open', 'Opens the bookmark in the system file explorer', 'bookmark')
def CmdOpenBookmark(bookmark: str) -> None:
    target = GetBookmarkPath(LoadBookmarkConfig(), bookmark)
    os.startfile(str(target))


@Command('list', 'Prints a list of all bookmarks')
def CmdListBookmarks() -> None:
    paths = LoadBookmarkConfig()
    if paths:
        maxLength = max([len(bookmark) for bookmark in paths])
        for bookmark, path in paths.items():
            print(f'{bookmark.ljust(maxLength)} -> {path}')
    else:
        print('No bookmarks available yet')


@Command('?', 'Prints a list of all commands')
def CmdListCommands() -> None:
    maxLength = max([len(cmd) for cmd in COMMANDS])
    for cmdInfo in COMMANDS.values():
        print(f'{cmdInfo.cmd.ljust(maxLength + 10)}{cmdInfo.description}')


def ExecCommand(args: Sequence[str]) -> None:
    parser = argparse.ArgumentParser(
        prog='go',
        usage='%(prog)s <bookmark> | <command> [<args>]',
        description='Navigate to a bookmark or manage directory bookmarks.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    for cmdInfo in COMMANDS.values():
        commandParser = subparsers.add_parser(
            cmdInfo.cmd, help=cmdInfo.description, description=cmdInfo.description
        )
        for argument in cmdInfo.arguments:
            commandParser.add_argument(argument)

    if not args:
        parser.print_usage()
        return

    options = parser.parse_args(args)
    cmdInfo = COMMANDS[options.command]
    cmdInfo.callback(*(getattr(options, argument) for argument in cmdInfo.arguments))


def GoTo(config: Dict[str, str], bookmark: str) -> None:
    print(GetBookmarkPath(config, bookmark))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        if not args or args[0] in COMMANDS or args[0].startswith('-'):
            ExecCommand(args)
        else:
            parser = argparse.ArgumentParser(prog='go')
            parser.add_argument('bookmark')
            options = parser.parse_args(args)
            GoTo(LoadBookmarkConfig(), options.bookmark)
    except (BookmarkError, OSError) as error:
        print(f'go: error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
