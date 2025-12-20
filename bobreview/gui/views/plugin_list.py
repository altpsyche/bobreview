"""
Plugin List View - Display and manage installed plugins.
"""

import flet as ft
from ..services import cli_wrapper


class PluginListView(ft.Container):
    """View for listing and managing plugins."""
    
    def __init__(self, page: ft.Page, on_create=None):
        super().__init__()
        self.page = page
        self.on_create = on_create
        self.expand = True
        self.padding = 20
        
        # Data table for plugins
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Version", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Description", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Directory", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=8,
            vertical_lines=ft.BorderSide(1, ft.Colors.GREY_800),
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_800),
        )
        
        # Loading indicator
        self.loading = ft.ProgressRing(visible=False)
        
        # Status text
        self.status_text = ft.Text("", color=ft.Colors.GREY_400)
        
        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Plugins", size=32, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Refresh",
                            icon=ft.Icons.REFRESH,
                            on_click=self._refresh_plugins,
                        ),
                        ft.ElevatedButton(
                            "Create New",
                            icon=ft.Icons.ADD,
                            on_click=lambda e: on_create() if on_create else None,
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(height=20),
                self.loading,
                self.status_text,
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
        self.page.update()
        
        try:
            plugins = cli_wrapper.list_plugins()
            
            self.data_table.rows = []
            for p in plugins:
                status = "Loaded" if p.loaded else "Available"
                status_color = ft.Colors.GREEN_400 if p.loaded else ft.Colors.GREY_400
                
                # Get directory path
                path_str = str(p.path) if hasattr(p, 'path') and p.path else "Unknown"
                
                self.data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(p.name, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(p.version or "1.0.0")),
                            ft.DataCell(ft.Text(p.description or "", max_lines=2)),
                            ft.DataCell(ft.Text(path_str, size=12, color=ft.Colors.GREY_400)),
                            ft.DataCell(ft.Text(status, color=status_color)),
                        ],
                    )
                )
            
            if plugins:
                self.status_text.value = f"Found {len(plugins)} plugin(s)"
            else:
                self.status_text.value = "No plugins found. Create one to get started!"
                
        except Exception as ex:
            self.status_text.value = f"Error loading plugins: {ex}"
            self.status_text.color = ft.Colors.RED_400
        
        self.loading.visible = False
        self.page.update()
