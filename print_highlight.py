from rich.text import Text
from rich.console import Console

console = Console()
text = Text.assemble(("Hello", "bold magenta"), " World!")
console.print(text)

from rich.tree import Tree
from rich import print

tree = Tree("Rich Tree")
tree.add('avc')
tree.add('[2m1s {py:1s js:2m}]\nef')
subtree = tree.add(
Text.assemble(("[2m1s {py:1s js:2m}]\n", "bold magenta"), " World!")
)
subtree.add(Text.assemble(("[2m1s]", "bold magenta"), " World!"))
subtree.add(Text.assemble(("[4MB] world", "red"), 'beta'), guide_style='red').add('c')
print(tree)