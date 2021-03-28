import os
import json
import sys
from pathlib import Path
from typing import Callable, Dict
from dataclasses import dataclass


@dataclass
class CommandInfo:
    cmd: str
    description: str
    usage: str
    callback: Callable[..., None]


CFG_FILE_PATH = Path(__file__).parent / 'go2.cfg'
COMMANDS: Dict[str, CommandInfo] = {}


def Command(name: str, description: str, usage: str = ''):
    def Decorator(func: Callable[..., None]):
        COMMANDS[name] = CommandInfo(name, description, usage, func)
        return func
    return Decorator


def LoadBookmarkConfig() -> Dict[str, str]:
    if not CFG_FILE_PATH.exists():
        WriteBookmarkConfig({})

    with open(CFG_FILE_PATH, 'r') as file:
        return json.loads(file.read())


def WriteBookmarkConfig(config: Dict[str, str]) -> None:
    with open(CFG_FILE_PATH, 'w') as file:
        file.write(json.dumps(config, indent=2))


@Command('add', 'Adds a new bookmark', 'Usage: add <bookmark> <target>')
def CmdAddBookmark(bookmark: str, targetPath: str) -> None:
    paths = LoadBookmarkConfig()
    if Path(targetPath).exists():
        paths[bookmark] = targetPath
        WriteBookmarkConfig(paths)
    else:
        print(f'"{targetPath}" is not a valid path')


@Command('del', 'Deletes a bookmark', 'Usage: del <bookmark>')
def CmdDelBookmark(bookmark: str) -> None:
    paths = LoadBookmarkConfig()
    paths.pop(bookmark, None)
    WriteBookmarkConfig(paths)


@Command('cfg', 'Opens the go2 configuration file')
def CmdOpenCfg() -> None:
    os.system(f'start {CFG_FILE_PATH}')


@Command('open', 'Opens the bookmark in the system file explorer', 'Usage: open <bookmark>')
def CmdOpenBookmark(bookmark: str) -> None:
    bookmarkConfig = LoadBookmarkConfig()
    if bookmark in bookmarkConfig:
        os.system(f'start {bookmarkConfig[bookmark]}')
    else:
        print(f'Unknown bookmark: {bookmark}')


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


def ExecCommand():
    try:
        COMMANDS[sys.argv[1]].callback(*sys.argv[2:])
    except KeyError:
        print(f'Unknown command: {sys.argv[1]}')
    except TypeError:
        print(COMMANDS[sys.argv[1]].usage)


def GoTo(config: Dict[str, str], bookmark: str) -> None:
    print(config[bookmark])


def main():
    bookmarkConfig = LoadBookmarkConfig()

    if len(sys.argv) > 1:
        if sys.argv[1] in bookmarkConfig:
            GoTo(bookmarkConfig, sys.argv[1])
        else:
            ExecCommand()
    else:
        print(f'Usage: go <bookmark> | <cmd> [<args>]')


if __name__ == '__main__':
    main()
