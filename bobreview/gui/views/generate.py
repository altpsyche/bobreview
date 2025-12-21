"""
Generate View - Report generation interface.
"""

import os
import flet as ft
import webbrowser
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
            on_change=self._on_plugin_changed,
        )
        
        # Theme dropdown (populated when plugin is selected)
        self.theme_dropdown = ft.Dropdown(
            label="Theme",
            width=200,
            options=[],
            value=None,
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
        
        # No cache checkbox
        self.no_cache_checkbox = ft.Checkbox(
            label="No Cache (regenerate LLM content)",
            value=False,
        )
        
        # Generate button (class attribute for enable/disable)
        self.generate_btn = ft.ElevatedButton(
            "Generate Report",
            icon=ft.Icons.PLAY_CIRCLE,
            on_click=self._generate_report,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
        )
        
        # Progress section
        self.progress_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.ProgressRing(width=20, height=20),
                    ft.Text("", size=14, ref=ft.Ref[ft.Text]()),
                ], spacing=10),
            ]),
            visible=False,
            padding=15,
            border_radius=8,
            bgcolor="#1e2632",
        )
        self.progress_text = ft.Text("", size=14)
        self.progress_ring = ft.ProgressRing(width=20, height=20)
        self.progress_container.content = ft.Row([
            self.progress_ring,
            self.progress_text,
        ], spacing=10)
        
        # Status
        self.status_text = ft.Text("", size=14)
        
        # Open report button (hidden initially)
        self.open_report_btn = ft.ElevatedButton(
            "Open Report",
            icon=ft.Icons.OPEN_IN_BROWSER,
            on_click=self._open_report,
            visible=False,
        )
        self.report_path = None
        
        # LLM warning banner
        self.llm_warning = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_400),
                ft.Text(
                    "No LLM API key configured. Go to LLM Settings to add one, or enable Dry Run.",
                    color=ft.Colors.ORANGE_400,
                    size=13,
                ),
            ], spacing=10),
            visible=False,
            padding=10,
            border_radius=8,
            bgcolor="#3d2e1f",
        )
        
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
                ft.Container(height=20),
                self.llm_warning,
                ft.Container(height=20),
                ft.Row([
                    self.plugin_dropdown,
                    self.theme_dropdown,
                ], spacing=15),
                ft.Container(height=15),
                ft.Row(
                    [
                        self.data_dir_field,
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=lambda e: self.data_dir_picker.get_directory_path(),
                            tooltip="Browse for data folder",
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
                            tooltip="Browse for output folder",
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
                            tooltip="Browse for config file",
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
                ft.Row([
                    self.dry_run_checkbox,
                    self.no_cache_checkbox,
                ], spacing=20),
                ft.Container(height=30),
                ft.Row(
                    [
                        self.generate_btn,
                        self.open_report_btn,
                    ],
                    spacing=10,
                ),
                ft.Container(height=15),
                self.progress_container,
                ft.Container(height=10),
                self.status_text,
            ],
        )
        
        # Load plugins and check LLM
        self._load_plugins()
        self._check_llm_config()
    
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
    
    def _check_llm_config(self):
        """Check if LLM API key is configured."""
        has_key = (
            os.environ.get("OPENAI_API_KEY") or
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("OLLAMA_BASE_URL")
        )
        self.llm_warning.visible = not has_key
        self.page.update()
    
    def _on_plugin_changed(self, e):
        """Handle plugin selection - load available themes."""
        if e.data:
            try:
                themes = cli_wrapper.get_plugin_themes(e.data)
                self.theme_dropdown.options = [
                    ft.dropdown.Option(t, t.capitalize()) for t in themes
                ]
                # Set default to first theme
                if themes:
                    self.theme_dropdown.value = themes[0]
                self.page.update()
            except Exception:
                # Fallback to default themes
                default = ['dungeon', 'midnight', 'aurora', 'sunset', 'frost']
                self.theme_dropdown.options = [
                    ft.dropdown.Option(t, t.capitalize()) for t in default
                ]
                self.theme_dropdown.value = 'dungeon'
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
    
    def _update_progress(self, message: str):
        """Update progress status."""
        self.progress_text.value = message
        self.page.update()
    
    def _generate_report(self, e):
        """Generate the report (starts async worker thread)."""
        import threading
        
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
        
        # Disable generate button during generation
        self.generate_btn.disabled = True
        
        # Show progress
        self.progress_container.visible = True
        self.open_report_btn.visible = False
        self.status_text.value = ""
        
        self._update_progress("Loading plugin...")
        
        # Capture params for thread
        params = {
            "plugin_name": self.plugin_dropdown.value,
            "data_dir": self.data_dir_field.value,
            "output_dir": self.output_dir_field.value,
            "config_path": self.config_field.value or None,
            "dry_run": self.dry_run_checkbox.value,
            "no_cache": self.no_cache_checkbox.value,
            "theme_id": self.theme_dropdown.value,
        }
        
        # Run in background thread
        thread = threading.Thread(target=self._run_generation, args=(params,))
        thread.daemon = True
        thread.start()
    
    def _run_generation(self, params: dict):
        """Run generation in background thread."""
        import traceback
        
        try:
            self._update_progress("Parsing data files...")
            
            # Check for LLM if not dry run
            if not params["dry_run"]:
                self._update_progress("Calling LLM for content generation...")
            
            result = cli_wrapper.generate_report(**params)
            
            self._update_progress("Writing report...")
            
            # Success - update UI
            self.progress_container.visible = False
            self.status_text.value = f"✓ Report generated: {result}"
            self.status_text.color = ft.Colors.GREEN_400
            
            # Store path and show open button
            self.report_path = result
            self.open_report_btn.visible = True
            
            # Show success snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Report generated successfully!"),
                action="Open",
                on_action=self._open_report,
            )
            self.page.snack_bar.open = True
            
        except Exception as ex:
            self.progress_container.visible = False
            self.status_text.value = f"Error: {ex}"
            self.status_text.color = ft.Colors.RED_400
            
            # Show detailed error dialog
            self._show_error_dialog(str(ex), traceback.format_exc())
        
        finally:
            # Re-enable button
            self.generate_btn.disabled = False
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
                ft.Text("Generation Failed"),
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
    
    def _open_report(self, e=None):
        """Open the generated report in browser."""
        if self.report_path:
            # Convert to file URL
            report_file = Path(str(self.report_path))
            if report_file.exists():
                webbrowser.open(f"file://{report_file.resolve()}")
            else:
                # Try as-is
                webbrowser.open(f"file://{self.report_path}")
