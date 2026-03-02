"""
Plugin List View - Display and manage installed plugins.
"""

import os
import flet as ft
import subprocess
import sys
from pathlib import Path
from ..services import cli_wrapper


class PluginListView(ft.Container):
    """View for listing and managing plugins."""
    
    def __init__(self, page: ft.Page, on_create=None):
        super().__init__()
        self._page = page
        self.on_create = on_create
        self.expand = True
        self.padding = 20
        
        # Add plugin folder picker
        self.add_plugin_picker = ft.FilePicker()
        self._page.services.append(self.add_plugin_picker)
        
        # Data table for plugins
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Version", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Description", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Location", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=8,
            vertical_lines=ft.BorderSide(1, ft.Colors.GREY_800),
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_800),
        )
        
        # Loading indicator
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)
        
        # Status text
        self.status_text = ft.Text("", color=ft.Colors.GREY_400)
        
        # Empty state
        self.empty_state = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.EXTENSION_OFF, size=64, color=ft.Colors.GREY_700),
                ft.Container(height=10),
                ft.Text("No plugins found", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                ft.Text("Create a new plugin or add an existing one", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "Create Plugin",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: on_create() if on_create else None,
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
                    ft.ElevatedButton(
                        "Add Existing",
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=self._pick_add_plugin_dir,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            visible=False,
            padding=40,
        )
        
        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Plugins", size=32, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        self.loading,
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            on_click=self._refresh_plugins,
                            tooltip="Refresh plugin list",
                        ),
                        ft.ElevatedButton(
                            "Add Existing",
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=self._pick_add_plugin_dir,
                            tooltip="Import an existing plugin folder",
                        ),
                        ft.ElevatedButton(
                            "Create New",
                            icon=ft.Icons.ADD,
                            on_click=lambda e: on_create() if on_create else None,
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                            tooltip="Create a new plugin from scratch",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(height=10),
                self.status_text,
                ft.Container(height=10),
                self.empty_state,
                ft.Container(
                    content=self.data_table,
                    expand=True,
                ),
            ],
            expand=True,
        )
        
        # Load plugins on init
        self._refresh_plugins(None)
    
    def _refresh_plugins(self, e):
        """Refresh the plugin list."""
        self.loading.visible = True
        self.status_text.value = "Loading plugins..."
        self._page.update()
        
        try:
            plugins = cli_wrapper.list_plugins()
            
            self.data_table.rows = []
            for p in plugins:
                # Get directory path
                path_str = str(p.path) if hasattr(p, 'path') and p.path else "Unknown"
                path_display = self._truncate_path(path_str, 40)
                
                # Store plugin data for details view
                plugin_data = {
                    "name": p.name,
                    "version": p.version or "1.0.0",
                    "description": p.description or "No description",
                    "path": path_str,
                    "capabilities": getattr(p, 'capabilities', []),
                }
                
                self.data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.TextButton(
                                    p.name,
                                    on_click=lambda e, data=plugin_data: self._show_plugin_details(data),
                                    style=ft.ButtonStyle(color=ft.Colors.BLUE_300),
                                )
                            ),
                            ft.DataCell(ft.Text(p.version or "1.0.0")),
                            ft.DataCell(
                                ft.Text(
                                    p.description or "No description",
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(path_display, size=12, color=ft.Colors.GREY_400, tooltip=path_str)
                            ),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.FOLDER_OPEN,
                                        icon_size=18,
                                        tooltip="Open folder",
                                        on_click=lambda e, path=path_str: self._open_folder(path),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_size=18,
                                        tooltip="Uninstall plugin",
                                        on_click=lambda e, name=p.name, path=path_str: self._confirm_uninstall(name, path),
                                    ),
                                ], spacing=0)
                            ),
                        ],
                    )
                )
            
            # Show/hide empty state
            if plugins:
                self.empty_state.visible = False
                self.data_table.visible = True
                self.status_text.value = f"Found {len(plugins)} plugin(s)"
            else:
                self.empty_state.visible = True
                self.data_table.visible = False
                self.status_text.value = ""
                
        except Exception as ex:
            self.status_text.value = f"Error loading plugins: {ex}"
            self.status_text.color = ft.Colors.RED_400
        
        self.loading.visible = False
        self._page.update()
    
    def _truncate_path(self, path: str, max_len: int) -> str:
        """Truncate path for display."""
        if len(path) <= max_len:
            return path
        return "..." + path[-(max_len - 3):]
    
    def _open_folder(self, path: str):
        """Open plugin folder in file explorer."""
        try:
            folder = Path(path)
            if folder.is_file():
                folder = folder.parent
            
            if sys.platform == "win32":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)])
            else:
                subprocess.run(["xdg-open", str(folder)])
        except Exception as ex:
            self._page.show_dialog(ft.SnackBar(
                content=ft.Text(f"Could not open folder: {ex}"),
                open=True,
            ))
    
    async def _pick_add_plugin_dir(self, e):
        """Open directory picker and handle result."""
        path = await self.add_plugin_picker.get_directory_path()
        if path:
            self._handle_add_plugin(path)

    def _handle_add_plugin(self, path: str):
        """Handle adding a plugin folder."""
        if path:
            plugin_path = Path(path)
            
            # Check if it looks like a plugin
            if not (plugin_path / "plugin.py").exists() and not (plugin_path / "__init__.py").exists():
                self._page.show_dialog(ft.SnackBar(
                    content=ft.Text("This doesn't look like a BobReview plugin folder (no plugin.py found)"),
                    bgcolor=ft.Colors.ORANGE_800,
                    open=True,
                ))
                return
            
            # Add to user plugins directory
            try:
                user_plugins_dir = Path.home() / ".bobreview" / "plugins"
                user_plugins_dir.mkdir(parents=True, exist_ok=True)
                
                # Create symlink or copy
                target = user_plugins_dir / plugin_path.name
                if target.exists():
                    self._page.show_dialog(ft.SnackBar(
                        content=ft.Text(f"Plugin '{plugin_path.name}' already exists"),
                        bgcolor=ft.Colors.ORANGE_800,
                        open=True,
                    ))
                else:
                    # Create symlink on Unix, copy on Windows
                    if sys.platform == "win32":
                        import shutil
                        shutil.copytree(str(plugin_path), str(target))
                    else:
                        target.symlink_to(plugin_path)
                    
                    self._page.show_dialog(ft.SnackBar(
                        content=ft.Text(f"Plugin '{plugin_path.name}' added successfully!"),
                        open=True,
                    ))
                    
                    # Refresh list
                    self._refresh_plugins(None)
                    
            except Exception as ex:
                self._page.show_dialog(ft.SnackBar(
                    content=ft.Text(f"Error adding plugin: {ex}"),
                    bgcolor=ft.Colors.RED_800,
                    open=True,
                ))
            
            self._page.update()
    
    def _confirm_uninstall(self, plugin_name: str, plugin_path: str):
        """Show confirmation dialog before uninstalling."""
        def close_dialog(e):
            self._page.pop_dialog()

        def do_uninstall(e):
            self._page.pop_dialog()
            self._uninstall_plugin(plugin_name, plugin_path)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Uninstall Plugin?"),
            content=ft.Text(f"Are you sure you want to uninstall '{plugin_name}'?\n\nThe plugin folder will be moved to trash."),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Uninstall",
                    on_click=do_uninstall,
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.show_dialog(dialog)

    def _uninstall_plugin(self, plugin_name: str, plugin_path: str):
        """Uninstall a plugin by moving it to trash."""
        import shutil
        import time
        
        try:
            path = Path(plugin_path)
            if path.is_file():
                path = path.parent
            
            if path.exists():
                # Move to ~/.bobreview/trash/ for recovery
                trash_dir = Path.home() / ".bobreview" / "trash"
                trash_dir.mkdir(parents=True, exist_ok=True)
                dest = trash_dir / f"{path.name}_{int(time.time())}"
                shutil.move(str(path), str(dest))
                
                self._page.show_dialog(ft.SnackBar(
                    content=ft.Text(f"Plugin '{plugin_name}' moved to ~/.bobreview/trash/"),
                    open=True,
                ))
                
                # Refresh list
                self._refresh_plugins(None)
            else:
                self._page.show_dialog(ft.SnackBar(
                    content=ft.Text("Plugin folder not found"),
                    bgcolor=ft.Colors.ORANGE_800,
                    open=True,
                ))

        except Exception as ex:
            self._page.show_dialog(ft.SnackBar(
                content=ft.Text(f"Failed to uninstall: {ex}"),
                bgcolor=ft.Colors.RED_800,
                open=True,
            ))

        self._page.update()
    
    def _show_plugin_details(self, plugin_data: dict):
        """Show plugin details dialog."""
        from ..services import cli_wrapper
        
        def close_dialog(e):
            self._page.pop_dialog()

        def open_folder(e):
            self._open_folder(plugin_data["path"])
        
        # Get themes for this plugin
        try:
            themes = cli_wrapper.get_plugin_themes(plugin_data["name"])
        except Exception:
            themes = []
        
        # Build capabilities list
        caps = plugin_data.get("capabilities", [])
        caps_text = ", ".join(caps) if caps else "None detected"
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.EXTENSION, color=ft.Colors.BLUE_300),
                ft.Text(plugin_data["name"]),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    # Version
                    ft.Row([
                        ft.Text("Version:", weight=ft.FontWeight.BOLD, width=100),
                        ft.Text(plugin_data["version"]),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    
                    # Description
                    ft.Row([
                        ft.Text("Description:", weight=ft.FontWeight.BOLD, width=100),
                        ft.Text(plugin_data["description"], expand=True),
                    ], vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    
                    # Path
                    ft.Row([
                        ft.Text("Path:", weight=ft.FontWeight.BOLD, width=100),
                        ft.Text(
                            plugin_data["path"],
                            size=12,
                            color=ft.Colors.GREY_400,
                            selectable=True,
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    
                    # Themes
                    ft.Row([
                        ft.Text("Themes:", weight=ft.FontWeight.BOLD, width=100),
                        ft.Text(", ".join(themes) if themes else "Default"),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    
                    # Capabilities
                    ft.Row([
                        ft.Text("Capabilities:", weight=ft.FontWeight.BOLD, width=100),
                        ft.Text(caps_text, size=12),
                    ]),
                ], spacing=10),
                width=500,
            ),
            actions=[
                ft.TextButton("Open Folder", icon=ft.Icons.FOLDER_OPEN, on_click=open_folder),
                ft.ElevatedButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self._page.show_dialog(dialog)
