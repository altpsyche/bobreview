"""
Plugin Create View - Wizard for creating new plugins.
"""

import flet as ft
from pathlib import Path
from ..services import cli_wrapper


class PluginCreateView(ft.Container):
    """Wizard for creating a new plugin."""
    
    def __init__(self, page: ft.Page, on_back=None):
        super().__init__()
        self.page = page
        self.on_back = on_back
        self.expand = True
        self.padding = 20
        
        # Form fields
        self.name_field = ft.TextField(
            label="Plugin Name",
            hint_text="e.g., my-plugin",
            width=400,
            autofocus=True,
        )
        
        self.template_dropdown = ft.Dropdown(
            label="Template",
            width=400,
            value="full",
            options=[
                ft.dropdown.Option("full", "Full - All features"),
                ft.dropdown.Option("minimal", "Minimal - Basic structure"),
            ],
        )
        
        self.output_dir_field = ft.TextField(
            label="Output Directory",
            hint_text="Leave empty for default (~/.bobreview/plugins/)",
            width=400,
        )
        
        # Status
        self.status_text = ft.Text("", size=14)
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)
        
        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: on_back() if on_back else None,
                        ),
                        ft.Text("Create New Plugin", size=32, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Container(height=30),
                ft.Text(
                    "Create a new BobReview plugin with scaffolder-generated code.",
                    size=16,
                    color=ft.Colors.GREY_400,
                ),
                ft.Container(height=30),
                self.name_field,
                ft.Container(height=15),
                self.template_dropdown,
                ft.Container(height=15),
                self.output_dir_field,
                ft.Container(height=30),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Create Plugin",
                            icon=ft.Icons.CREATE_NEW_FOLDER,
                            on_click=self._create_plugin,
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                        ),
                        self.loading,
                    ],
                    spacing=10,
                ),
                ft.Container(height=20),
                self.status_text,
            ],
        )
    
    def _create_plugin(self, e):
        """Handle plugin creation."""
        name = self.name_field.value.strip()
        
        if not name:
            self.status_text.value = "Please enter a plugin name"
            self.status_text.color = ft.Colors.RED_400
            self.page.update()
            return
        
        # Validate name format
        if not name.replace('-', '').replace('_', '').isalnum():
            self.status_text.value = "Plugin name should only contain letters, numbers, hyphens and underscores"
            self.status_text.color = ft.Colors.RED_400
            self.page.update()
            return
        
        self.loading.visible = True
        self.status_text.value = "Creating plugin..."
        self.status_text.color = ft.Colors.GREY_400
        self.page.update()
        
        try:
            output_dir = self.output_dir_field.value.strip() or None
            if output_dir:
                output_dir = Path(output_dir).expanduser().resolve()
            
            created_path = cli_wrapper.create_plugin(
                name=name,
                output_dir=output_dir,
                template=self.template_dropdown.value,
            )
            
            self.status_text.value = f"✓ Created plugin at: {created_path}"
            self.status_text.color = ft.Colors.GREEN_400
            
            # Show success dialog
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Plugin '{name}' created successfully!"),
                action="View Plugins",
                on_action=lambda e: self.on_back() if self.on_back else None,
            )
            self.page.snack_bar.open = True
            
        except Exception as ex:
            self.status_text.value = f"Error: {ex}"
            self.status_text.color = ft.Colors.RED_400
        
        self.loading.visible = False
        self.page.update()
