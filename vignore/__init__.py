# this version is for pyjom, our ultimate challenge.
# TODO: type "R" to refresh the tree
# TODO: filter empty files using fd
# TODO: visualize unselected files by calling fd -u

# TODO: add visualization of tree files.
# TODO: add action to restart the processing thread

# TODO: show the relative path of the selected item in the file tree

# to find empty files:
# fd -S "-1b"

# filter out empty files:
# fd -S "+1b"

# TODO: use with git, mark files excluded by ignore but included in git, and included by ignore but not added by git

# TODO: use docopt, add copy command to copy files that are not ignored to a new destination

# TODO: fix label renderable content not updating issue (is it because of incompatible textual version?)

# TODO: customize the look of vscode, background, app icon for this specific project, "vignore"

import humanize
import numpy
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Label, Static
from rich.text import Text
from textual.timer import Timer
from threading import Lock
from jinja2 import Template
from argparse import ArgumentParser
from beartype import beartype
from datetime import datetime, timedelta
from collections import defaultdict
import os
import aiofiles
import asyncio

cached_paths = []

INTERVAL = 0.1
SLEEP = 7


def format_timedelta(td: timedelta):
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes}:{seconds}"


def estimate_time_from_lines(line_count: int):
    seconds = (line_count / 35) * 60
    return seconds


def naturaltime(seconds: float):
    return humanize.naturaltime(timedelta(seconds=seconds)).split(" ago")[0]


def estimate_time_from_filesize(filesize: int):
    seconds = (filesize / 1000) * 60
    return seconds


# TODO: remove dead code
script_template_str = """
cd "{{diffpath}}"
fd --no-ignore --hidden | tree --fromfile > "{{tempdir}}/all_tree.txt"
fd | tree --fromfile > "{{tempdir}}/selected_tree.txt"
diff -y "{{tempdir}}/all_tree.txt" "{{tempdir}}/selected_tree.txt" > "{{tempdir}}/diff_tree.txt"
cat "{{tempdir}}/diff_tree.txt"
"""


# tree output in json
# load tree json, set selected & unselected properties
# count file size
# render tree json

script_template = Template(script_template_str)

RELATIVE_TEMP_DIR_SCRIPT_PATH = "script.sh"


def expand_parent(elem):
    elem.expand()
    if not elem.is_root:
        expand_parent(elem.parent)


async def count_lines_text(file_path: str):
    count = 0
    async with aiofiles.open(file_path, "r") as fp:  # Async context manager
        async for _ in fp:  # Asynchronous line iteration
            count += 1
    return count


async def _async_count_chunks(reader, chunk_size):
    """Async generator to yield chunks of data"""
    while True:
        chunk = await reader(chunk_size)
        if not chunk:
            break
        yield chunk


async def count_lines_binary(file_path: str):
    chunk_size = 1024 * 1024  # 1MB chunks
    count = 0
    async with aiofiles.open(file_path, "rb") as fp:
        # Create async generator for chunks
        chunk_generator = _async_count_chunks(fp.read, chunk_size)

        # Process each chunk as it's read
        async for chunk in chunk_generator:
            count += chunk.count(b"\n")

    # Preserve original +1 behavior
    return count + 1


async def read_file_and_get_line_count(filepath: str):
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        return -1
    if filepath in cached_paths:
        return -3
    try:
        readable = False
        async with aiofiles.open(filepath, mode="r", encoding="utf-8") as f:
            _ = await f.readline()
            readable = True
        if readable:
            lc = 0
            lc = await count_lines_binary(filepath)
            return lc if lc else 1
    except:
        return -2


# def patch_missing_files(path, basemap, expand=False, ):
def patch_missing_files(path, basemap, expand=False, processor=lambda x: x):
    subpath, filename = dirsplit(path)
    # breakpoint()
    if basemap.get(path) is None:
        subtree, _, _ = patch_missing_files(subpath + "/", basemap, processor=processor)
        # renderable = Text.assemble((processor(filename), color))
        if path.endswith("/"):
            subsubtree = subtree.add(processor(filename), expand=expand)
        else:
            subsubtree = subtree.add_leaf(processor(filename))
        # subsubtree = subtree.add(processor(filename), expanded=expanded,style=color, guide_style=color)
        # print(filename)
        basemap[path] = subsubtree
        return subsubtree, filename, False
    else:
        return basemap.get(path), filename, True


async def get_file_size(filename):
    try:
        async with aiofiles.open(filename, mode="rb") as file:
            file_size = os.fstat(file.fileno()).st_size
            return file_size
    except:
        return -1


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--diffpath",
        help="Path to visualize ignored files",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-c", "--copy", help="Path to copy files filtered by ignore rules to", type=str
    )
    parser.add_argument(
        "-i", "--inverse", help="Inverse the ignore rules", action="store_true"
    )
    parser.add_argument("-y", "--dryrun", help="Dry run", action="store_true")
    args = parser.parse_args()
    return args


def dirsplit(path):
    if path.endswith("/"):
        path = path[:-1]
    return os.path.split(path)


def iterate_parent_dirs(path):
    parts = path.split("/")
    for i in range(1, len(parts)):
        yield "/".join(parts[:i]) + "/", parts[i - 1]


# TODO: remove dead code
@beartype
def render_script_template(diffpath: str, tempdir: str) -> str:
    return script_template.render(diffpath=diffpath, tempdir=tempdir)


# processingLock = Lock()
def get_node_name(node):
    node_text = node.label._text[0]
    if node_text.startswith("<"):
        node_name = node_text.split(">", 1)[1].lstrip(" ")
    elif node_text.startswith("["):
        node_name = node_text.split("]", 1)[1].lstrip(" ")
    elif node_text.startswith("("):
        node_name = node_text.split(")", 1)[1].lstrip(" ")
    else:
        node_name = node_text
    return node_name


def get_full_path(node, result="") -> str:
    node_name = get_node_name(node)
    result = node_name + "/" + result
    if not node.is_root:
        return get_full_path(node.parent, result=result)
    else:
        return result


class CustomTree(Tree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        # self.app.notify(f"highlighted: {event.node}")
        highlighted_node = event.node
        if highlighted_node:
            node_full_path = get_full_path(highlighted_node)  # could have / in the end
            if not highlighted_node._children:
                node_full_path = node_full_path.rstrip("/")
            self.app.update_addressline(node_full_path)
            # self.app.notify(f"highlighted: {node_full_path}")


class VisualIgnoreApp(App):
    """A Textual app to visualize ignore files."""

    BINDINGS = [
        # ("d", "toggle_dark", "Toggle dark mode"),
        ("e", "exit", "Exit"),
        ("r", "restart", "Restart"),
        ("t", "toggle_label", "Toggle label"),
        # TODO: toggle label display
    ]
    timer: Timer

    def action_restart(self):
        self.loop_break = True

    def action_toggle_label(self, refresh=True):
        self.label.visible = not self.label.visible
        if not self.label.visible:
            self.label.styles.max_height = 0
        else:
            self.label.styles.max_height = None
        if refresh:
            self.label.recompose()
            self.label.refresh()

    def update_addressline(self, address: str):
        self.treeview_addressline.update(Text.assemble(address))

    def __init__(self, diffpath: str, fd_bin_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processingLock = Lock()
        self.title = "vignore"
        self.header = Header()
        self.fd_bin_path = fd_bin_path
        self.diffpath = diffpath
        self.treeview = CustomTree(".")
        # do not expand, since this is slow.
        self.treeview.root.expand()
        self.treeview_addressline = Label(Text.assemble("./"), expand=True)
        self.treeview_addressline.styles.background = "green"

        self.footer = Footer(show_command_palette=False)
        self.mymap = {"./": self.treeview.root}
        # self.counter = 0
        default_label = "Processing time: -/- (lines) -/- (size)\nLines: -/- Size: -/- Count: -/- Errors: -/-\nLast selection: - Selection: -/-\nTotal size: -/- Total count: -/- Errors: -/-\nLast scanning: - Scanning: -/-"
        self.label = Label(Text.assemble((default_label, "bold")), expand=True)
        self.action_toggle_label(refresh=False)
        self.label.styles.background = "green"
        # self.label.visible=False
        # self.label.styles.max_height=0
        # self.label.styles.border = ('solid','red')
        # self.label.styles.height = 3
        self.label.styles.height = 5
        # self.label.styles.dock = 'bottom'
        self.processing_time_by_line = 0
        self.processing_time_by_size = 0
        self.previous_processing_time_by_line = "-"
        self.previous_processing_time_by_size = "-"
        self.line_count_map = defaultdict(int)
        self.size_map = defaultdict(int)
        self.error_size_map = defaultdict(int)
        self.line_count = 0
        self.previous_line_count = "-"
        self.error_count_map = defaultdict(int)
        self.error_count = 0
        self.previous_error_count = "-"
        self.previous_time = datetime.now()
        self.previous_selection_formatted = "-"
        self.previous_scanning_formatted = "-"
        self.previous_selection = "-"
        self.selected_paths = {"./"}
        self.existing_paths = {"./"}
        self.previous_selected_paths = {"./"}
        self.previous_existing_paths = {"./"}
        self.error_size_count = 0
        self.previous_error_size_count = "-"
        self.previous_scanning = "-"
        self.error_count_type_map = defaultdict(int)
        self.filesize = 0
        self.previous_filesize = "-"
        self.loop_break = False
        self.selected_size = 0
        self.previous_selected_size = "-"
        self.selected_count = 0
        self.previous_selected_count = "-"
        self.total_count = 0
        self.previous_total_count = "-"

    async def progress(self):
        locked = self.processingLock.acquire(blocking=False)
        if locked:  # taking forever. bad.
            self.processing_time_by_line = 0
            self.processing_time_by_size = 0
            self.selected_count = 0
            # self.previous_selected_count = "-"
            self.total_count = 0
            # self.previous_total_count = "-"

            self.line_count = 0
            self.selected_size = 0
            # self.previous_selected_size = "-"
            self.filesize = 0
            self.loop_break = False
            self.selected_paths = {"./"}
            self.existing_paths = {"./"}
            self.line_count_map = defaultdict(int)
            self.error_count_map = defaultdict(int)
            self.error_count_type_map = defaultdict(int)
            self.size_map = defaultdict(int)
            self.error_size_map = defaultdict(int)
            self.error_count = 0
            self.error_size_count = 0
            self.previous_time = datetime.now()
            # command = [self.fd_bin_path, "-S", "+1b"]
            command = compile_fd_list_files_cmd(self.fd_bin_path)
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, cwd=self.diffpath
            )
            banner_refresh_counter = 0
            while not self.loop_break:
                line = await process.stdout.readline()  # type:ignore
                if not line:
                    break
                decline = line.decode("utf-8").strip()
                if decline == "":
                    break
                relpath = "./" + decline
                self.selected_paths.add(relpath)
                subtree, fname, _ = patch_missing_files(relpath, self.mymap)
                if not relpath.endswith("/"):
                    self.selected_count += 1
                    linecount = await read_file_and_get_line_count(
                        os.path.join(self.diffpath, relpath)
                    )
                    fs_str = "error"
                    fs = await get_file_size(os.path.join(self.diffpath, relpath))
                    if fs != -1:
                        fs_str = humanize.naturalsize(fs)
                        self.filesize += fs
                        self.selected_size += fs

                    for parent_path, parent_name in iterate_parent_dirs(
                        relpath
                    ):  # ends with "/"
                        self.selected_paths.add(parent_path)
                        if fs != -1:
                            self.size_map[parent_path] += fs
                    error = True
                    if linecount == 0:
                        label = "Empty"
                    elif linecount == -1:
                        label = "Missing"
                    elif linecount == -2:
                        label = "Error"
                    elif linecount == -3:
                        label = "Cached"
                        error = False
                    else:
                        label = f"{linecount} L"
                        self.line_count += linecount
                        self.line_count_map[relpath] = linecount
                        for parent_path, parent_name in iterate_parent_dirs(
                            relpath
                        ):  # ends with "/"
                            self.line_count_map[parent_path] += linecount
                            # self.selected_paths.add(parent_path)
                            if parent_path not in self.error_count_map.keys():
                                lb = (
                                    f"[{self.line_count_map[parent_path]} L, {humanize.naturalsize(self.size_map[parent_path])}] "
                                    + parent_name
                                )
                                pn = self.mymap.get(parent_path, None)
                                # if pn is None:
                                # breakpoint()
                                # with open("error.txt", "w+") as f:
                                # f.write(parent_path+" should in "+str(self.mymap.keys()))
                                #     self.exit()
                                # else:
                                pn.set_label(lb)
                        error = False
                    color = "white"
                    if error:
                        color = "bold red"
                        expand_parent(subtree)
                        self.error_count += 1
                        self.error_count_type_map[label] += 1

                        for parent_path, parent_name in iterate_parent_dirs(
                            relpath
                        ):  # ends with "/"
                            self.error_count_map[parent_path] += 1
                            # self.selected_paths.add(parent_path)
                            self.mymap[parent_path].set_label(
                                Text.assemble(
                                    (
                                        f"<{self.error_count_map[parent_path]} E> "
                                        + parent_name,
                                        "bold red",
                                    )
                                )
                            )
                    if not error:
                        label_prefix = f"[{label}, {fs_str}]"
                    else:
                        label_prefix = f"<{label}>"
                        # if fs_str == "error":
                        #     label_prefix = f"<{label}>"
                        # else:
                        #     label_prefix = f"<{label}, {fs_str}>"
                    subtree.set_label(
                        Text.assemble(
                            (
                                label_prefix + f" {fname}",
                                color,
                            )
                        )
                    )
                banner_refresh_counter += 1
                if banner_refresh_counter > 1:
                    # if banner_refresh_counter > 10000:
                    banner_refresh_counter = 0
                    running = format_timedelta(datetime.now() - self.previous_time)
                    self.processing_time_by_line = naturaltime(
                        estimate_time_from_lines(self.line_count)
                    )
                    self.processing_time_by_size = naturaltime(
                        estimate_time_from_filesize(self.selected_size)
                    )
                    self.label.update(
                        Text.assemble(
                            (
                                f"Processing time: {self.processing_time_by_line}/{self.previous_processing_time_by_line} (lines) {self.processing_time_by_size}/{self.previous_processing_time_by_size} (size)\nLines: {self.line_count}/{self.previous_line_count} Size: {humanize.naturalsize(self.selected_size)}/{self.previous_selected_size} Count: {self.selected_count}/{self.previous_selected_count} Errors: {self.error_count}/{self.previous_error_count}\nLast selection: {self.previous_selection_formatted} Selection: {running}/{self.previous_selection}\nTotal size: -/{self.previous_filesize} Total count: -/{self.previous_total_count} Errors: -/{self.previous_error_size_count}\nLast scanning: {self.previous_scanning_formatted} Scanning: -/{self.previous_scanning}",
                                "bold",
                            )
                        )
                    )
            # not_selected = 0
            if self.loop_break:
                try:
                    process.terminate()
                except:
                    pass
            else:
                map_keys = numpy.array(list(self.mymap.keys()))
                # map_keys = set(self.mymap.keys())
                not_selected_paths = numpy.setdiff1d(
                    map_keys, numpy.array(list(self.selected_paths))
                )
                not_selected_paths_real = numpy.setdiff1d(
                    not_selected_paths, numpy.array(list(self.previous_selected_paths))
                )
                # with open("not_selected.txt", "w+") as f:
                #     f.write(str(not_selected_paths_real))
                #     self.exit()
                for k in not_selected_paths_real:
                    _, fname = dirsplit(k)
                    self.mymap[k].set_label(Text.assemble((fname, "bright_black")))
                # breakpoint()
                self.previous_selected_paths = self.selected_paths
                self.previous_processing_time_by_line = self.processing_time_by_line
                self.previous_processing_time_by_size = self.processing_time_by_size
                self.previous_line_count = self.line_count
                self.previous_selected_count = self.selected_count
                self.previous_selected_size = humanize.naturalsize(self.selected_size)
                self.previous_error_count = self.error_count
                self.previous_selection = format_timedelta(
                    datetime.now() - self.previous_time
                )
                self.previous_time = datetime.now()
                self.previous_selection_formatted = self.previous_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                await process.wait()
                # clear those nonselected paths, mark as grey
                # now for another step
                # command2 = [self.fd_bin_path, "-u", "-S", "+1b"]
                command2 = compile_fd_list_files_cmd(
                    self.fd_bin_path, unrestricted=True
                )
                process2 = await asyncio.create_subprocess_exec(
                    *command2, stdout=asyncio.subprocess.PIPE, cwd=self.diffpath
                )
                banner_refresh_counter = 0
                while not self.loop_break:
                    line = await process2.stdout.readline()  # type:ignore
                    if not line:
                        break
                    decline = line.decode("utf-8").strip()
                    if decline == "":
                        break
                    banner_refresh_counter += 1
                    relpath = "./" + decline
                    self.existing_paths.add(relpath)
                    # subtree, fname = patch_missing_files(relpath, self.mymap)
                    subtree, fname, _ = patch_missing_files(
                        relpath,
                        self.mymap,
                        processor=lambda x: Text.assemble((x, "bright_black")),
                    )
                    if not relpath.endswith("/"):
                        self.total_count += 1
                        for parent_path, parent_name in iterate_parent_dirs(
                            relpath
                        ):  # ends with "/"
                            self.existing_paths.add(parent_path)
                        if relpath not in self.selected_paths:
                            if (
                                os.path.join(self.diffpath, relpath)
                                not in self.size_map.keys()
                            ):
                                filesize = await get_file_size(
                                    os.path.join(self.diffpath, relpath)
                                )
                                if filesize != -1:
                                    self.filesize += filesize

                            else:
                                filesize = self.size_map[
                                    os.path.join(self.diffpath, relpath)
                                ]
                            if filesize != -1:
                                filesize_str = humanize.naturalsize(filesize)
                                subtree.set_label(
                                    Text.assemble(
                                        (f"({filesize_str}) {fname}", "bright_black")
                                    )
                                )
                                for parent_path, parent_name in reversed(
                                    list(iterate_parent_dirs(relpath))
                                ):
                                    # self.existing_paths.add(parent_path)
                                    # if "0.json" in relpath:
                                    #     with open('debug.txt', 'w+') as f:
                                    #         f.write(str(self.selected_paths)+"\n")
                                    #         f.write(parent_path+" "+parent_name+"\n")
                                    #         f.write(str(relpath)+"\n")
                                    #         self.exit()
                                    if parent_path not in self.selected_paths:
                                        self.size_map[parent_path] += filesize
                                        if (
                                            parent_path
                                            not in self.error_size_map.keys()
                                        ):
                                            self.mymap[parent_path].set_label(
                                                Text.assemble(
                                                    (
                                                        f"({humanize.naturalsize(self.size_map[parent_path])}) {parent_name}",
                                                        "bright_black",
                                                    )
                                                )
                                            )
                                    else:
                                        break
                            else:  # propagate error?
                                subtree.set_label(
                                    Text.assemble(
                                        ("(error)", "bold red"),
                                        (f"{fname}", "bright_black"),
                                    )
                                )
                                self.error_size_count += 1

                                for parent_path, parent_name in reversed(
                                    list(iterate_parent_dirs(relpath))
                                ):  # ends with "/"
                                    # self.existing_paths.add(parent_path)
                                    if parent_path not in self.selected_paths:
                                        self.error_size_map[parent_path] += 1
                                        self.mymap[parent_path].set_label(
                                            Text.assemble(
                                                (
                                                    f"({self.error_size_map[parent_path]} errors) ",
                                                    "bold red",
                                                ),
                                                (parent_name, "bright_black"),
                                            )
                                        )
                                    else:
                                        break

                    banner_refresh_counter += 1
                    if banner_refresh_counter > 1:
                        # if banner_refresh_counter > 10000:
                        banner_refresh_counter = 0
                        running = format_timedelta(datetime.now() - self.previous_time)
                        self.label.update(
                            Text.assemble(
                                (
                                    f"Processing time: -/{self.previous_processing_time_by_line} (lines) -/{self.previous_processing_time_by_size} (size)\nLines: -/{self.previous_line_count} Size: -/{self.previous_selected_size} Count: -/{self.previous_selected_count} Errors: -/{self.previous_error_count}\nLast selection: {self.previous_selection_formatted} Selection: -/{self.previous_selection}\nTotal size: {humanize.naturalsize(self.filesize)}/{self.previous_filesize} Total count: {self.total_count}/{self.previous_total_count} Errors: {self.error_size_count}/{self.previous_error_size_count}\nLast scanning: {self.previous_scanning_formatted} Scanning: {running}/{self.previous_scanning}",
                                    "bold",
                                )
                            )
                        )
                if self.loop_break:
                    try:
                        process2.terminate()
                    except:
                        pass
                else:
                    map_keys = numpy.array(list(self.mymap.keys()))
                    remove_keys = numpy.setdiff1d(
                        map_keys, numpy.array(list(self.existing_paths))
                    )
                    # breakpoint()
                    # with open('remove_keys.txt', 'w+') as f:
                    #     f.write(str(remove_keys))
                    #     self.exit()

                    for k in remove_keys:
                        try:
                            self.mymap[k].remove()
                        except:
                            pass
                        finally:
                            del self.mymap[k]
                    self.previous_existing_paths = self.existing_paths
                    self.previous_total_count = self.total_count
                    self.previous_filesize = humanize.naturalsize(self.filesize)
                    self.previous_error_size_count = self.error_size_count
                    self.previous_scanning = format_timedelta(
                        datetime.now() - self.previous_time
                    )
                    self.previous_scanning_formatted = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    self.previous_time = datetime.now()
                await process2.wait()
                # clear nonexisting paths
                await asyncio.sleep(SLEEP)

            self.processingLock.release()

        # self.counter += 1

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        return [
            self.header,
            self.treeview_addressline,
            self.treeview,
            self.label,
            self.footer,
        ]

    def on_mount(self) -> None:
        self.timer = self.set_interval(INTERVAL, self.progress)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_exit(self):
        """An action to exit the app."""
        self.exit()


def set_event_loop():
    import sys

    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

def check_fd_installed():
    import shutil
    import platform

    if platform.platform().lower() == "windows":
        fd_shorthand = "fd.exe"
    else:
        fd_shorthand = "fd"

    fd_bin_path = shutil.which(fd_shorthand)
    assert (
        fd_bin_path
    ), "Binary 'fd' not in PATH. Please install from https://github.com/sharkdp/fd/releases/latest"
    return fd_bin_path


def copy_single_file_to_destination(source_path: str, target_path: str, dry_run: bool):
    import shutil

    if os.path.isdir(source_path):
        if not dry_run:
            os.makedirs(target_path, exist_ok=True)
        print(f"making directory at: {target_path}")
    elif os.path.isfile(source_path):
        if not dry_run:
            shutil.copy2(source_path, target_path)
        print(f"copied {source_path} to {target_path}")
    else:
        print(
            f"warning: source path {source_path} is not a file or directory, so ignored"
        )


def delete_single_file_from_destination(target_path: str, dry_run: bool):
    import os

    if os.path.isdir(target_path):
        if not os.listdir(target_path):
            if not dry_run:
                # only delete empty directory
                os.rmdir(target_path)
            print(f"deleted empty directory at: {target_path}")
        else:
            print(
                f"warning: target directory path {target_path} is not empty, so ignored"
            )
    elif os.path.isfile(target_path):
        if not dry_run:
            os.remove(target_path)
        print(f"deleted {target_path}")
    else:
        print(
            f"warning: target path {target_path} is not a file or directory, so ignored"
        )


def compile_fd_list_files_cmd(fd_bin_path: str, unrestricted: bool = False):
    if unrestricted:
        cmd = [fd_bin_path, "-u", "-S", "+1b"]
    else:
        cmd = [fd_bin_path, "-S", "+1b"]
    return cmd


def fd_list_files(diffpath: str, fd_bin_path: str, respect_ignore_rules: bool):
    import subprocess

    unrestricted = not respect_ignore_rules
    cmd = compile_fd_list_files_cmd(fd_bin_path, unrestricted=unrestricted)
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=diffpath, text=True
    )
    for line in process.stdout:
        yield line.strip()


def perform_copy_operation(
    diffpath: str, fd_bin_path: str, inverse: bool, copy_target_dir: str, dry_run: bool
):
    assert os.path.isdir(diffpath), f"Directory {diffpath} does not exist"
    assert os.path.isdir(copy_target_dir), f"Directory {copy_target_dir} does not exist"
    if inverse:
        # inverse operation shall be performed like:
        # copy all files to destination
        # delete non-ignored files from destination
        for path in fd_list_files(diffpath, fd_bin_path, respect_ignore_rules=False):
            source_path = os.path.join(diffpath, path)
            dest_path = os.path.join(copy_target_dir, path)
            copy_single_file_to_destination(source_path, dest_path, dry_run=dry_run)
        for path in fd_list_files(
            copy_target_dir, fd_bin_path, respect_ignore_rules=True
        ):
            dest_path = os.path.join(copy_target_dir, path)
            delete_single_file_from_destination(dest_path, dry_run=dry_run)
    else:
        for path in fd_list_files(diffpath, fd_bin_path, respect_ignore_rules=True):
            source_path = os.path.join(diffpath, path)
            dest_path = os.path.join(copy_target_dir, path)
            copy_single_file_to_destination(source_path, dest_path, dry_run=dry_run)


def launch_vignore_app(diffpath: str, fd_bin_path: str):
    set_event_loop()
    app = VisualIgnoreApp(diffpath=diffpath, fd_bin_path=fd_bin_path)
    app.run()


def main():
    args = parse_args()
    diffpath = args.diffpath
    copy_target_dir = args.copy
    inverse = args.inverse
    dry_run = args.dryrun
    fd_bin_path = check_fd_installed()
    if copy_target_dir:
        # perform copy operation
        perform_copy_operation(
            diffpath=diffpath,
            fd_bin_path=fd_bin_path,
            inverse=inverse,
            copy_target_dir=copy_target_dir,
            dry_run=dry_run,
        )
    else:
        launch_vignore_app(diffpath=diffpath, fd_bin_path=fd_bin_path)
