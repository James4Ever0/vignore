from rich.text import Text
from rich.console import Console
# color from: 
from rich.color import ANSI_COLOR_NAMES
console = Console()
from rich.tree import Tree
from rich import print

tree = Tree("agi_computer_control")
tree.add('folder0')
tree.add('[2m1s {py:1s js:2m}]\nfolder1')
subtree = tree.add(
Text.assemble(("[2m1s {py:1s js:2m}]\n", "light_yellow3"), "folder2")
)
subtree.add(Text.assemble(("[2m1s]", "bold magenta"), " file.js"))
subsubtree = subtree.add("[4MB {py:4MB}]\nworld", style='gray3', guide_style='gray3')
subsubtree.add('[4MB] cent.py')
print(tree)

text = Text.assemble(("ETA:", "bold magenta"), " 2m1s")
console.print(text)
