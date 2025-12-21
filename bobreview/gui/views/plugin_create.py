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
            hint_text="e.g., my-awesome-plugin",
            width=400,
            autofocus=True,
            on_change=self._validate_name,
        )
        
        self.name_validation = ft.Text("", size=12)
        
        self.template_dropdown = ft.Dropdown(
            label="Template",
            width=400,
            value="full",
            options=[
                ft.dropdown.Option("full", "Full - All features (recommended)"),
                ft.dropdown.Option("minimal", "Minimal - Basic structure"),
            ],
        )
        
        self.output_dir_field = ft.TextField(
            label="Output Directory",
            hint_text="Leave empty for default (~/.bobreview/plugins/)",
            width=400,
            read_only=True,
        )
        
        # File picker for output directory
        self.output_dir_picker = ft.FilePicker(
            on_result=self._on_output_dir_picked,
        )
        page.overlay.append(self.output_dir_picker)
        
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
                            tooltip="Back to plugin list",
                        ),
                        ft.Text("Create New Plugin", size=32, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Container(height=10),
                ft.Text(
                    "Create a new BobReview plugin with scaffolder-generated code.",
                    size=16,
                    color=ft.Colors.GREY_400,
                ),
                ft.Container(height=30),
                
                # Plugin name with validation
                ft.Container(
                    content=ft.Column([
                        self.name_field,
                        self.name_validation,
                    ], spacing=5),
                ),
                ft.Container(height=15),
                
                # Template selection
                self.template_dropdown,
                ft.Container(height=15),
                
                # Output directory with browse button
                ft.Row(
                    [
                        self.output_dir_field,
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=lambda e: self.output_dir_picker.get_directory_path(),
                            tooltip="Browse for output folder",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            on_click=self._clear_output_dir,
                            tooltip="Use default location",
                        ),
                    ],
                    spacing=5,
                ),
                ft.Container(height=30),
                
                # Create button
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
    
    def _on_output_dir_picked(self, e: ft.FilePickerResultEvent):
        """Handle output directory selection."""
        if e.path:
            self.output_dir_field.value = e.path
            self.page.update()
    
    def _clear_output_dir(self, e):
        """Clear output directory (use default)."""
        self.output_dir_field.value = ""
        self.page.update()
    
    def _validate_name(self, e):
        """Validate plugin name in real-time."""
        name = self.name_field.value.strip()
        if not name:
            self.name_validation.value = ""
            self.name_validation.color = ft.Colors.GREY_400
        elif not name.replace('-', '').replace('_', '').isalnum():
            self.name_validation.value = "⚠ Only letters, numbers, hyphens, and underscores"
            self.name_validation.color = ft.Colors.ORANGE_400
        elif len(name) < 3:
            self.name_validation.value = "⚠ Name should be at least 3 characters"
            self.name_validation.color = ft.Colors.ORANGE_400
        else:
            self.name_validation.value = "✓ Valid name"
            self.name_validation.color = ft.Colors.GREEN_400
        self.page.update()
    
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
            import traceback
            self.status_text.value = f"Error: {ex}"
            self.status_text.color = ft.Colors.RED_400
            self._show_error_dialog(str(ex), traceback.format_exc())
        
        self.loading.visible = False
        self.page.update()
    
    def _show_error_dialog(self, message: str, details: str):
        """Show a detailed error dialog."""
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        def copy_details(e):
            self.page.set_clipboard(details)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Error details copied to clipboard"),
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_400),
                ft.Text("Plugin Creation Failed"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(message, size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Text("Details:", size=12, color=ft.Colors.GREY_400),
                    ft.Container(
                        content=ft.Text(
                            details[:500] + ("..." if len(details) > 500 else ""),
                            size=11,
                            color=ft.Colors.GREY_500,
                            selectable=True,
                        ),
                        bgcolor="#1e2632",
                        padding=10,
                        border_radius=8,
                    ),
                ], scroll=ft.ScrollMode.AUTO),
                width=500,
                height=300,
            ),
            actions=[
                ft.TextButton("Copy Details", on_click=copy_details),
                ft.ElevatedButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
