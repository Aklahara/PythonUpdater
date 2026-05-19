import re

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, DataTable, ListView, ListItem, Static

from versions import PythonRelease, PythonMajorVersion, BuildFlags, build_major_version_data, _version_tuple

YES = "[green]✓[/green]"
NO = "[red]✗[/red]"
NA = "[dim]—[/dim]"

_MARKUP_RE = re.compile(r'\[[^]]*]')

# (label, column_key, width)
COL_DEFS = [
    ("Version", "version", 7),
    ("Installed", "installed", 9),
    ("Update", "update", 10),
    ("PGO", "pgo", 5),
    ("LTO", "lto", 5),
    ("✗ GIL", "no_gil", 5),
    ("JIT", "jit", 5),
    ("", "install", 10),
]


def flag(value: bool) -> str:
    return YES if value else NO


def center_right(markup: str, width: int) -> str:
    """Center markup text in `width` chars; odd remainder goes to the right."""
    n = len(_MARKUP_RE.sub('', markup))
    excess = width - n
    if excess <= 0:
        return markup
    left = excess // 2
    right = excess - left
    return " " * left + markup + " " * right


class MainHeader(Static):
    DEFAULT_CSS = """
    MainHeader {
        dock: top;
        height: 1;
        background: $panel;
        color: $foreground;
        text-align: center;
        text-style: bold;
    }
    """

    def on_mount(self) -> None:
        self.update(self.app.TITLE)



class VersionSelectScreen(ModalScreen):
    """Modal that lists all minor versions for a major_version."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("i", "install", "Install"),
    ]

    CSS = """
    VersionSelectScreen { align: center middle; }
    #modal-container {
        width: 50; height: auto; max-height: 80%;
        border: solid $primary; background: $surface; padding: 1 2;
    }
    #modal-title  { text-align: center; text-style: bold; margin-bottom: 1; }
    #version-list { height: auto; max-height: 20; }
    #modal-hint   { text-align: center; color: $text-muted; margin-top: 1; }
    """

    def __init__(self, major_version: PythonMajorVersion) -> None:
        super().__init__()
        self.major_version = major_version

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="modal-container"):
            yield Label(f"Python {self.major_version.major_version} — select version", id="modal-title")
            items = []
            for r in self.major_version.releases:
                tags = []
                if r.version == self.major_version.installed_version:
                    tags.append("[green]installed[/green]")
                if r.version == self.major_version.latest:
                    tags.append("[cyan]latest[/cyan]")
                if r.prerelease:
                    tags.append("[magenta]pre-release[/magenta]")
                suffix = f"  ({', '.join(tags)})" if tags else ""
                items.append(ListItem(
                    Label(f"{r.version}{suffix}"),
                    name=r.version,
                    disabled=(r.version == self.major_version.installed_version),
                ))
            yield ListView(*items, id="version-list")
            yield Label("[bold]Enter[/bold] / [bold]I[/bold] Select   [bold]Esc[/bold] Close", id="modal-hint")

    def action_install(self) -> None:
        lv: ListView = self.query_one("#version-list", ListView)
        if lv.highlighted_child is None:
            return
        version_str = lv.highlighted_child.name
        release = next((r for r in self.major_version.releases if r.version == version_str), None)
        if release:
            self.dismiss(release)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        version_str = event.item.name
        release = next((r for r in self.major_version.releases if r.version == version_str), None)
        if release:
            self.dismiss(release)


def _flag_cell(desired_val: bool, installed_val: bool) -> str:
    if desired_val == installed_val:
        return YES if desired_val else NO
    return f"[yellow]{'✓' if desired_val else '✗'}[/yellow]"


class MainApp(App):
    theme = "ansi-dark"
    TITLE = "Python Updater"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+q", "noop", "", show=False),
        Binding("r", "refresh", "Refresh"),
        Binding("i", "install_selected", "Install", show=False),
        Binding("backspace", "revert_row", "Revert", show=False),
        Binding("1", "toggle_pgo", "Toggle PGO", show=False),
        Binding("2", "toggle_lto", "Toggle LTO", show=False),
        Binding("3", "toggle_gil", "Toggle GIL", show=False),
        Binding("4", "toggle_jit", "Toggle JIT", show=False),
    ]
    CSS = """
    #status { height: 1; padding: 0 1; color: $text-muted; }
    #loading { height: 1fr; }
    #version-table { height: 1fr; display: none; }
    """

    def compose(self) -> ComposeResult:
        yield MainHeader()
        yield Label("Fetching release information...", id="status")
        yield LoadingIndicator(id="loading")
        yield DataTable(id="version-table", cursor_type="row", zebra_stripes=True)
        # yield Footer()

    def on_mount(self) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        self._col_widths: dict[str, int] = {key: w for _, key, w in COL_DEFS}
        for label, key, width in COL_DEFS:
            table.add_column(Text(label, justify="center"), width=width, key=key)
        self.load_versions()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _supports_nogil_jit(self, mv: PythonMajorVersion) -> bool:
        major, minor = map(int, mv.major_version.split("."))
        return (major, minor) >= (3, 13)

    def _row_needs_action(self, mv: PythonMajorVersion) -> bool:
        """True if installing the target version or changing flags is pending."""
        target = self._desired_versions.get(mv.major_version, mv.latest)
        if target and target != mv.installed_version:
            return True
        if not mv.installed_version:
            return False
        desired = self._desired_flags.get(mv.major_version, BuildFlags())
        installed = mv.build_flags or BuildFlags()
        if desired.optimizations != installed.optimizations:
            return True
        if desired.lto != installed.lto:
            return True
        if self._supports_nogil_jit(mv):
            if desired.no_gil != installed.no_gil:
                return True
            if desired.jit != installed.jit:
                return True
        return False

    def _make_row_cells(self, pmv: PythonMajorVersion) -> list[Text]:
        installed = pmv.installed_version or NA

        target = self._desired_versions.get(pmv.major_version, pmv.latest)
        if not pmv.installed_version:
            update_cell = f"[cyan][underline]↓[/underline] {target}[/cyan]" if target else NA
        elif target == pmv.installed_version:
            update_cell = "[green]Newest[/green]"
        elif target and _version_tuple(target) > _version_tuple(pmv.installed_version):
            update_cell = f"[yellow bold]↑ {target}[/yellow bold]"
        else:
            update_cell = f"[yellow bold]↓ {target}[/yellow bold]"

        desired = self._desired_flags.get(pmv.major_version, BuildFlags())
        installed_flags = pmv.build_flags or BuildFlags()
        pre313 = not self._supports_nogil_jit(pmv)

        pgo_c = _flag_cell(desired.optimizations, installed_flags.optimizations)
        lto_c = _flag_cell(desired.lto, installed_flags.lto)
        no_gil_c = NA if pre313 else _flag_cell(desired.no_gil, installed_flags.no_gil)
        jit_c = NA if pre313 else _flag_cell(desired.jit, installed_flags.jit)

        if installed != NA:
            install_c = "[bold green]▶ Update[/bold green]" if self._row_needs_action(pmv) else ""
        else:
            install_c = "[bold green]▶ Download[/bold green]"

        w = self._col_widths

        def left(m: str) -> Text:
            return Text.from_markup(m, justify="left")

        def ctr(m: str, col: str) -> Text:
            return Text.from_markup(center_right(m, w[col]), justify="left")

        return [
            left(f"[bold]{pmv.major_version}[/bold]"),
            left(installed),
            ctr(update_cell, "update") if update_cell == "[green]Newest[/green]" else left(update_cell),
            ctr(pgo_c, "pgo"),
            ctr(lto_c, "lto"),
            ctr(no_gil_c, "no_gil"),
            ctr(jit_c, "jit"),
            left(install_c),
        ]

    def _refresh_row(self, pmv: PythonMajorVersion) -> None:
        table = self.query_one("#version-table", DataTable)
        cells = self._make_row_cells(pmv)
        for (_, col_key, _), cell in zip(COL_DEFS, cells):
            table.update_cell(pmv.major_version, col_key, cell)

    # ── data loading ──────────────────────────────────────────────────────────

    @work(thread=True)
    def load_versions(self) -> None:
        major_version_list = build_major_version_data()
        self.call_from_thread(self._populate_table, major_version_list)

    def _populate_table(self, major_version_list: list[PythonMajorVersion]) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        table.clear()
        self._major_version_list = major_version_list

        # Initialise desired flags and versions once; preserve across refreshes
        if not hasattr(self, "_desired_flags"):
            self._desired_flags: dict[str, BuildFlags] = {}
        if not hasattr(self, "_desired_versions"):
            self._desired_versions: dict[str, str | None] = {}
        for mv in major_version_list:
            if mv.major_version not in self._desired_versions:
                self._desired_versions[mv.major_version] = mv.latest
            if mv.major_version not in self._desired_flags:
                bf = mv.build_flags
                self._desired_flags[mv.major_version] = BuildFlags(
                    optimizations=bf.optimizations if bf else False,
                    lto=bf.lto if bf else False,
                    no_gil=bf.no_gil if bf else False,
                    jit=bf.jit if bf else False,
                )

        for mv in major_version_list:
            table.add_row(*self._make_row_cells(mv), key=mv.major_version)

        self.query_one("#loading").display = False
        self.query_one("#status", Label).update(
            f"[dim]{len(major_version_list)} versions loaded — "
            f"[bold]Enter[/bold] select  [bold]I[/bold] install  "
            f"[bold]1-4[/bold] toggle PGO/LTO/GIL/JIT  [bold]R[/bold] refresh[/dim]"
        )
        table.display = True
        table.focus()

    # ── toggle actions ────────────────────────────────────────────────────────

    def _toggle_flag(self, field: str, requires_313: bool = False) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        if table.cursor_row < 0 or not hasattr(self, "_major_version_list"):
            return
        mv = self._major_version_list[table.cursor_row]
        if requires_313 and not self._supports_nogil_jit(mv):
            return
        desired = self._desired_flags.get(mv.major_version, BuildFlags())
        setattr(desired, field, not getattr(desired, field))
        self._desired_flags[mv.major_version] = desired
        self._refresh_row(mv)

    def action_toggle_pgo(self) -> None:
        self._toggle_flag("optimizations")

    def action_toggle_lto(self) -> None:
        self._toggle_flag("lto")

    def action_toggle_gil(self) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        if table.cursor_row < 0 or not hasattr(self, "_major_version_list"):
            return
        mv = self._major_version_list[table.cursor_row]
        if not mv.installed_version or not self._supports_nogil_jit(mv):
            return
        desired = self._desired_flags.get(mv.major_version, BuildFlags())
        desired.no_gil = not desired.no_gil
        if desired.no_gil:
            desired.jit = False  # GIL-off and JIT are mutually exclusive
        self._desired_flags[mv.major_version] = desired
        self._refresh_row(mv)

    def action_toggle_jit(self) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        if table.cursor_row < 0 or not hasattr(self, "_major_version_list"):
            return
        mv = self._major_version_list[table.cursor_row]
        if not mv.installed_version or not self._supports_nogil_jit(mv):
            return
        desired = self._desired_flags.get(mv.major_version, BuildFlags())
        desired.jit = not desired.jit
        if desired.jit:
            desired.no_gil = False  # JIT and GIL-off are mutually exclusive
        self._desired_flags[mv.major_version] = desired
        self._refresh_row(mv)

    # ── install action ────────────────────────────────────────────────────────

    def action_install_selected(self) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        if table.cursor_row < 0 or not hasattr(self, "_major_version_list"):
            return
        mv = self._major_version_list[table.cursor_row]
        if not self._row_needs_action(mv):
            return
        target_version = self._desired_versions.get(mv.major_version, mv.latest)
        release = next(
            (r for r in mv.releases if r.version == target_version),
            mv.releases[0],
        )
        desired = self._desired_flags.get(mv.major_version, BuildFlags())
        self.query_one("#status", Label).update(
            f"[cyan]Launching installer for Python {release.version}...[/cyan]"
        )
        self._run_installer(release, desired)

    # ── misc actions ──────────────────────────────────────────────────────────

    def action_noop(self) -> None:
        pass

    def action_revert_row(self) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        if table.cursor_row < 0 or not hasattr(self, "_major_version_list"):
            return
        mv = self._major_version_list[table.cursor_row]
        self._desired_versions[mv.major_version] = mv.latest
        bf = mv.build_flags
        self._desired_flags[mv.major_version] = BuildFlags(
            optimizations=bf.optimizations if bf else False,
            lto=bf.lto if bf else False,
            no_gil=bf.no_gil if bf else False,
            jit=bf.jit if bf else False,
        )
        self._refresh_row(mv)
        self.query_one("#status", Label).update(
            f"[dim]Reverted Python {mv.major_version} to defaults.[/dim]"
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if not hasattr(self, "_major_version_list"):
            return
        mv = self._major_version_list[event.cursor_row]
        self.push_screen(VersionSelectScreen(mv), self._on_version_selected)

    def _on_version_selected(self, release: PythonRelease | None) -> None:
        if release is None:
            return
        parts = release.version.split(".")
        major_ver = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else None
        if not major_ver:
            return
        self._desired_versions[major_ver] = release.version
        mv = next((m for m in self._major_version_list if m.major_version == major_ver), None)
        if mv:
            self._refresh_row(mv)
        self.query_one("#status", Label).update(
            f"[cyan]Target set to Python {release.version}. Press [bold]I[/bold] to install.[/cyan]"
        )

    def action_refresh(self) -> None:
        table: DataTable = self.query_one("#version-table", DataTable)
        table.display = False
        table.clear()
        self.query_one("#loading").display = True
        self.query_one("#status", Label).update("Fetching release information...")
        self.load_versions()

    @work(thread=True)
    def _run_installer(self, release: PythonRelease, desired_flags: BuildFlags | None = None) -> None:
        import subprocess
        flags = desired_flags or BuildFlags()
        flag_args: list[str] = []
        if flags.optimizations: flag_args.append("--pgo")
        if flags.lto:           flag_args.append("--lto")
        if flags.no_gil:        flag_args.append("--no-gil")
        if flags.jit:           flag_args.append("--jit")
        flags_str = " ".join(flag_args)
        cmd = [
            "gnome-terminal", "--wait", "--",
            "bash", "-c",
            f"./InstallPython.sh {release.tarball_url} {release.version} {flags_str}; "
            f"read -p 'Press Enter to close...'"
        ]
        subprocess.run(cmd)
        self.call_from_thread(
            self.query_one("#status", Label).update,
            f"[green]Installer for Python {release.version} finished.[/green]"
        )


if __name__ == "__main__":
    MainApp().run()
