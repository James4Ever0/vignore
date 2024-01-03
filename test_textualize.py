from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Label, Rule
from rich.text import Text
from textual.timer import Timer

class StopwatchApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("e", "exit", "Exit")]
    timer: Timer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.header = Header()
        self.treeview = RichLog(auto_scroll=False)
        self.footer = Footer()
        self.counter = 0
        self.label = Label(Text.assemble(('data','bold')),expand=True)
        self.label.styles.background = 'red'
        # self.label.styles.border = ('solid','red')
        # self.label.styles.height = 3
        self.label.styles.height = 1
        # self.label.styles.dock = 'bottom'
        

    def progress(self):
        self.treeview.clear()
        for l in range(300):
            self.treeview.write(str(self.counter)+":"+str(l)) # newline by default.
        self.label.renderable = "ETA: "+str(self.counter)
        self.label.refresh()
        self.counter += 1

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        return [self.header, self.treeview,self.label, self.footer]
        # return [self.header, self.treeview,self.rule, self.label, self.footer]

    def on_mount(self) -> None:
        self.timer = self.set_interval(1 / 5, self.progress)

    def on_ready(self):
        ...
        # self.treeview.write("hello world\n" * 200)
        # self.treeview.write(Text.assemble(("hello world\n", "red")))
        # self.treeview.write("hello world\n")
        # self.treeview.write(f"offset: {self.treeview.scroll_offset}")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_exit(self):
        """An action to exit the app."""
        self.exit()


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()
