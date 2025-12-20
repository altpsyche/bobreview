"""
Generate View - Report generation interface.
"""

import flet as ft
from pathlib import Path
from ..services import cli_wrapper


class GenerateView(ft.Container):
    """View for generating reports."""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = 20
        
        # Plugin dropdown
        self.plugin_dropdown = ft.Dropdown(
            label="Plugin",
            width=400,
            options=[],
        )
        
        # Data directory picker
        self.data_dir_field = ft.TextField(
            label="Data Directory",
            hint_text="Select folder containing your data",
            width=400,
            read_only=True,
        )
        self.data_dir_picker = ft.FilePicker(
            on_result=self._on_data_dir_picked,
        )
        
        # Output directory picker
        self.output_dir_field = ft.TextField(
            label="Output Directory",
            hint_text="Where to save the report",
            width=400,
            read_only=True,
        )
        self.output_dir_picker = ft.FilePicker(
            on_result=self._on_output_dir_picked,
        )
        
        # Config file picker (optional)
        self.config_field = ft.TextField(
            label="Config YAML (Optional)",
            hint_text="Custom report configuration",
            width=400,
            read_only=True,
        )
        self.config_picker = ft.FilePicker(
            on_result=self._on_config_picked,
        )
        
        # Dry run checkbox
        self.dry_run_checkbox = ft.Checkbox(
            label="Dry Run (skip LLM calls)",
            value=False,
        )
        
        # Status
        self.status_text = ft.Text("", size=14)
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)
        
        # Add file pickers to page overlay
        page.overlay.extend([
            self.data_dir_picker,
            self.output_dir_picker,
            self.config_picker,
        ])
        
        self.content = ft.Column(
            [
                ft.Text("Generate Report", size=32, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Text(
                    "Select a plugin and data directory to generate a report.",
                    size=16,
                    color=ft.Colors.GREY_400,
                ),
                ft.Container(height=30),
                self.plugin_dropdown,
                ft.Container(height=15),
                ft.Row(
                    [
                        self.data_dir_field,
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=lambda e: self.data_dir_picker.get_directory_path(),
                        ),
                    ],
                    spacing=5,
                ),
                ft.Container(height=15),
                ft.Row(
                    [
                        self.output_dir_field,
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=lambda e: self.output_dir_picker.get_directory_path(),
                        ),
                    ],
                    spacing=5,
                ),
                ft.Container(height=15),
                ft.Row(
                    [
                        self.config_field,
                        ft.IconButton(
                            icon=ft.Icons.FILE_OPEN,
                            on_click=lambda e: self.config_picker.pick_files(
                                allowed_extensions=["yaml", "yml"],
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            on_click=self._clear_config,
                            tooltip="Clear config",
                        ),
                    ],
                    spacing=5,
                ),
                ft.Container(height=15),
                self.dry_run_checkbox,
                ft.Container(height=30),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Generate Report",
                            icon=ft.Icons.PLAY_CIRCLE,
                            on_click=self._generate_report,
                            bgcolor=ft.Colors.GREEN_700,
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
        
        # Load plugins
        self._load_plugins()
    
    def _load_plugins(self):
        """Load available plugins into dropdown."""
        try:
            plugins = cli_wrapper.list_plugins()
            self.plugin_dropdown.options = [
                ft.dropdown.Option(p.name, p.name)
                for p in plugins
            ]
            if plugins:
                self.plugin_dropdown.value = plugins[0].name
        except Exception as ex:
            self.status_text.value = f"Error loading plugins: {ex}"
            self.status_text.color = ft.Colors.RED_400
        self.page.update()
    
    def _on_data_dir_picked(self, e: ft.FilePickerResultEvent):
        """Handle data directory selection."""
        if e.path:
            self.data_dir_field.value = e.path
            self.page.update()
    
    def _on_output_dir_picked(self, e: ft.FilePickerResultEvent):
        """Handle output directory selection."""
        if e.path:
            self.output_dir_field.value = e.path
            self.page.update()
    
    def _on_config_picked(self, e: ft.FilePickerResultEvent):
        """Handle config file selection."""
        if e.files:
            self.config_field.value = e.files[0].path
            self.page.update()
    
    def _clear_config(self, e):
        """Clear config field."""
        self.config_field.value = ""
        self.page.update()
    
    def _generate_report(self, e):
        """Generate the report."""
        # Validate inputs
        if not self.plugin_dropdown.value:
            self.status_text.value = "Please select a plugin"
            self.status_text.color = ft.Colors.RED_400
            self.page.update()
            return
        
        if not self.data_dir_field.value:
            self.status_text.value = "Please select a data directory"
            self.status_text.color = ft.Colors.RED_400
            self.page.update()
            return
        
        if not self.output_dir_field.value:
            self.status_text.value = "Please select an output directory"
            self.status_text.color = ft.Colors.RED_400
            self.page.update()
            return
        
        self.loading.visible = True
        self.status_text.value = "Generating report..."
        self.status_text.color = ft.Colors.GREY_400
        self.page.update()
        
        try:
            result = cli_wrapper.generate_report(
                plugin_name=self.plugin_dropdown.value,
                data_dir=self.data_dir_field.value,
                output_dir=self.output_dir_field.value,
                config_path=self.config_field.value or None,
                dry_run=self.dry_run_checkbox.value,
            )
            
            self.status_text.value = f"✓ Report generated: {result}"
            self.status_text.color = ft.Colors.GREEN_400
            
            # Show success snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Report generated successfully!"),
            )
            self.page.snack_bar.open = True
            
        except Exception as ex:
            self.status_text.value = f"Error: {ex}"
            self.status_text.color = ft.Colors.RED_400
        
        self.loading.visible = False
        self.page.update()
