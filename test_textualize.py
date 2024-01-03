from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log


class StopwatchApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        h = Header()
        t = Log()
        t.write("hello world\n")
        t.write("hello world\n")
        # t.clear()
        t.write(f"offset: {t.scroll_offset}")
        # t.scroll_offset.x
        # t.scroll_offset.y
        # t = Tree('.')
        f = Footer()
        return [h, t, f]

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()
