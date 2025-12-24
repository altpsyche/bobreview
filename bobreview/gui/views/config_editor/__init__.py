"""
Config Editor View - Visual editor for report_config.yaml.

This module provides the main ConfigEditorView class, which orchestrates
the page and component editing experience. The actual dialog logic is
delegated to the dialogs module for better separation of concerns.

Allows non-technical users to:
- Add/remove/reorder pages
- Add/remove/edit components
- Configure themes
- Preview reports in browser
"""

import os
import yaml
import flet as ft
import webbrowser
from pathlib import Path
from typing import List, Dict, Any, Optional

from ...services import cli_wrapper
from .data_reader import DataReader
from .expression_helper import ExpressionHelper
from .dialogs import PageEditorDialog, ComponentEditorDialog


class ConfigEditorView(ft.Container):
    """Visual editor for report_config.yaml."""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = 20
        
        # State
        self.current_config: Dict[str, Any] = {}
        self.config_path: Optional[Path] = None
        self.available_components: List[dict] = []
        
        # History for undo/redo
        self._history: List[Dict[str, Any]] = []
        self._history_index: int = -1
        self._max_history: int = 50
        
        # Helpers
        self.data_reader = DataReader()
        self.expression_helper = ExpressionHelper()
        
        # UI Elements
        self._init_ui_elements()
        self._build_ui()
    
    def _init_ui_elements(self):
        """Initialize UI elements."""
        self.plugin_dropdown = ft.Dropdown(
            label="Plugin",
            width=300,
            options=[],
            on_change=self._on_plugin_changed,
        )
        
        self.data_dir_field = ft.TextField(
            label="Data Directory",
            hint_text="Required for preview",
            width=300,
            read_only=True,
        )
        self.data_dir_picker = ft.FilePicker(
            on_result=self._on_data_dir_picked,
        )
        
        self.theme_dropdown = ft.Dropdown(
            label="Theme",
            width=200,
            options=[],
        )
        
        self.title_field = ft.TextField(
            label="Report Title",
            width=400,
        )
        
        self.pages_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        
        self.status_text = ft.Text("", size=14)
        
        self.save_btn = ft.ElevatedButton(
            "Save Config",
            icon=ft.Icons.SAVE,
            on_click=self._save_config,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
        )
        
        self.preview_btn = ft.ElevatedButton(
            "Preview in Browser",
            icon=ft.Icons.PREVIEW,
            on_click=self._preview,
        )
        
        self.add_page_btn = ft.ElevatedButton(
            "Add Page",
            icon=ft.Icons.ADD,
            on_click=self._add_page,
        )
        
        self.reload_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Reload plugin (clear cache)",
            on_click=self._reload_plugin,
        )
        
        self.undo_btn = ft.IconButton(
            icon=ft.Icons.UNDO,
            tooltip="Undo (Ctrl+Z)",
            on_click=self._undo,
            disabled=True,
        )
        
        self.redo_btn = ft.IconButton(
            icon=ft.Icons.REDO,
            tooltip="Redo (Ctrl+Y)",
            on_click=self._redo,
            disabled=True,
        )
    
    def _build_ui(self):
        """Build the editor UI."""
        self.content = ft.Column(
            [
                ft.Text("Config Editor", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Edit your report configuration visually",
                    size=14,
                    color=ft.Colors.GREY_400,
                ),
                ft.Container(height=20),
                
                # Plugin and data selector
                ft.Row([
                    self.plugin_dropdown,
                    self.reload_btn,
                    self.data_dir_field,
                    ft.ElevatedButton(
                        "Browse",
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda e: self.data_dir_picker.get_directory_path(),
                    ),
                ], spacing=10),
                
                ft.Container(height=20),
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                ft.Container(height=20),
                
                # Config fields
                ft.Row([
                    self.title_field,
                    self.theme_dropdown,
                ], spacing=20),
                
                ft.Container(height=20),
                
                # Pages header
                ft.Row([
                    ft.Text("Pages", size=18, weight=ft.FontWeight.BOLD),
                    self.add_page_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                
                # Pages list
                ft.Container(
                    content=self.pages_column,
                    height=400,
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    border_radius=8,
                    padding=10,
                ),
                
                ft.Container(height=20),
                
                # Action buttons
                ft.Row([
                    self.undo_btn,
                    self.redo_btn,
                    ft.Container(width=20),  # Spacer
                    self.save_btn,
                    self.preview_btn,
                ], spacing=10),
                
                ft.Container(height=10),
                self.status_text,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        self.page.overlay.append(self.data_dir_picker)
    
    def on_mount(self):
        """Called when view is mounted."""
        self._load_plugins()
    
    def _load_plugins(self):
        """Load available plugins."""
        try:
            plugins = cli_wrapper.list_plugins()
            self.plugin_dropdown.options = [
                ft.dropdown.Option(p.name, p.name) for p in plugins
            ]
            self.page.update()
        except Exception as ex:
            self._set_status(f"Error loading plugins: {ex}", "red")
    
    def _on_plugin_changed(self, e):
        """Handle plugin selection."""
        plugin_name = e.data
        if not plugin_name:
            return
        
        try:
            # Load themes
            themes = cli_wrapper.get_plugin_themes(plugin_name)
            self.theme_dropdown.options = [
                ft.dropdown.Option(t, t.capitalize()) for t in themes
            ]
            
            # Load components
            self.available_components = cli_wrapper.get_plugin_components(plugin_name)
            
            # Load data fields for expression helper
            data_fields = cli_wrapper.get_plugin_data_fields(plugin_name)
            if data_fields:
                self.expression_helper.set_columns(data_fields)
            
            # Build warnings for missing plugin features
            warnings = []
            if not self.available_components:
                warnings.append("COMPONENT_TYPES not defined - cannot add/edit components")
            if not themes:
                warnings.append("THEME_NAMES not defined - no themes available")
            if not data_fields:
                warnings.append("DATA_FIELDS not defined - expression helper limited")
            
            if warnings:
                self._set_status(f"⚠️ Plugin needs update: {'; '.join(warnings)}", "orange")
            
            # Find and load config
            plugins = cli_wrapper.list_plugins()
            plugin = next((p for p in plugins if p.name == plugin_name), None)
            
            if plugin and plugin.path:
                plugin_dir = Path(plugin.path)
                if plugin_dir.is_file():
                    plugin_dir = plugin_dir.parent
                
                config_path = plugin_dir / "report_config.yaml"
                if config_path.exists():
                    self.config_path = config_path
                    self._load_config(config_path)
                    if not warnings:
                        self._set_status(f"✓ Loaded config from {config_path.name}", "green")
                else:
                    self._set_status("No report_config.yaml found", "orange")
            
            self.page.update()
            
        except Exception as ex:
            import traceback
            self._show_error_dialog(
                "Plugin Load Error",
                f"Failed to load plugin '{plugin_name}'",
                traceback.format_exc()
            )
    
    def _load_config(self, config_path: Path):
        """Load config from YAML file with validation."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.current_config = yaml.safe_load(f) or {}
        
        # Validate config structure
        validation_errors = self._validate_config(self.current_config)
        if validation_errors:
            self._show_error_dialog(
                "Config Validation Warning",
                f"Found {len(validation_errors)} issue(s) in config",
                "\n".join(validation_errors)
            )
        
        self.title_field.value = self.current_config.get('name', '')
        
        theme = self.current_config.get('theme', 'dungeon')
        if self.theme_dropdown.options:
            self.theme_dropdown.value = theme
        
        self._render_pages()
        
        # Save initial state to history
        self._history.clear()
        self._history_index = -1
        self._push_history()
    
    def _validate_config(self, config: dict) -> list:
        """Validate config structure, return list of errors."""
        errors = []
        
        if 'pages' not in config:
            errors.append("Missing 'pages' key - config requires at least one page")
            return errors
        
        pages = config.get('pages', [])
        if not pages:
            errors.append("No pages defined")
            return errors
        
        for i, page in enumerate(pages):
            page_id = page.get('id', f'page_{i}')
            
            if 'id' not in page:
                errors.append(f"Page {i+1}: missing 'id'")
            if 'title' not in page:
                errors.append(f"Page '{page_id}': missing 'title'")
            
            for j, comp in enumerate(page.get('components', [])):
                if 'type' not in comp:
                    errors.append(f"Page '{page_id}', Component {j+1}: missing 'type'")
        
        return errors
    
    def _render_pages(self):
        """Render pages list."""
        self.pages_column.controls.clear()
        
        pages = self.current_config.get('pages', [])
        for i, page_data in enumerate(pages):
            self.pages_column.controls.append(
                self._create_page_card(i, page_data)
            )
        
        if not pages:
            self.pages_column.controls.append(
                ft.Text("No pages yet. Click 'Add Page' to create one.",
                       color=ft.Colors.GREY_500, italic=True)
            )
    
    def _create_page_card(self, index: int, page_data: dict) -> ft.Container:
        """Create a card for a page."""
        page_id = page_data.get('id', f'page_{index}')
        page_title = page_data.get('title', 'Untitled')
        components = page_data.get('components', [])
        
        comp_preview = ", ".join([c.get('type', '?').split('_')[-1] for c in components[:3]])
        if len(components) > 3:
            comp_preview += f", +{len(components) - 3} more"
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ARTICLE, color=ft.Colors.BLUE_300),
                    ft.Text(page_title, weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        tooltip="Edit page",
                        icon_size=18,
                        on_click=lambda e, idx=index: self._edit_page(idx),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Delete page",
                        icon_size=18,
                        on_click=lambda e, idx=index: self._delete_page(idx),
                    ),
                ]),
                ft.Text(f"ID: {page_id}", size=12, color=ft.Colors.GREY_500),
                ft.Text(f"Components: {comp_preview or 'None'}", size=12, color=ft.Colors.GREY_400),
            ]),
            padding=15,
            bgcolor="#1e2632",
            border_radius=8,
        )
    
    def _reload_plugin(self, e):
        """Reload current plugin by clearing cache."""
        if not self.plugin_dropdown.value:
            self._set_status("No plugin selected", "orange")
            return
        
        from ..services.plugin_loader import PluginLoader
        PluginLoader.clear_cache()
        
        # Re-trigger plugin load
        class FakeEvent:
            data = self.plugin_dropdown.value
        
        self._on_plugin_changed(FakeEvent())
        self._set_status("✓ Plugin reloaded", "green")
    
    def _on_data_dir_picked(self, e: ft.FilePickerResultEvent):
        """Handle data directory selection."""
        if e.path:
            self.data_dir_field.value = e.path
            
            # Load columns using DataReader
            if self.data_reader.read_directory(e.path):
                self.expression_helper.set_columns(self.data_reader.columns)
            
            message, color = self.data_reader.get_status_message()
            self._set_status(message, color)
            self.page.update()
    
    def _add_page(self, e):
        """Add a new page."""
        pages = self.current_config.setdefault('pages', [])
        new_page = {
            'id': f'page_{len(pages) + 1}',
            'title': f'New Page {len(pages) + 1}',
            'icon': 'fa-file',
            'layout': 'single-column',
            'nav_order': len(pages) + 1,
            'components': [],
        }
        pages.append(new_page)
        self._push_history()
        self._render_pages()
        self.page.update()
        self._edit_page(len(pages) - 1)
    
    def _delete_page(self, index: int):
        """Delete a page."""
        pages = self.current_config.get('pages', [])
        if 0 <= index < len(pages):
            pages.pop(index)
            self._push_history()
            self._render_pages()
            self.page.update()
    
    def _edit_page(self, index: int):
        """Open page editor dialog."""
        pages = self.current_config.get('pages', [])
        if not (0 <= index < len(pages)):
            return
        
        page_data = pages[index]
        
        dialog = PageEditorDialog(
            page=self.page,
            page_data=page_data,
            page_index=index,
            available_components=self.available_components,
            on_save=lambda: (self._push_history(), self._render_pages(), self.page.update()),
            on_edit_component=lambda comp_idx: self._edit_component(index, comp_idx),
        )
        dialog.show()
    
    def _edit_component(self, page_idx: int, comp_idx: int):
        """Edit a component's properties."""
        pages = self.current_config.get('pages', [])
        if not (0 <= page_idx < len(pages)):
            return
        
        page_data = pages[page_idx]
        components = page_data.get('components', [])
        if not (0 <= comp_idx < len(components)):
            return
        
        comp = components[comp_idx]
        comp_type = comp.get('type', 'unknown')
        
        # Find component definition
        comp_def = next((c for c in self.available_components if c['type'] == comp_type), None)
        
        # Try matching without plugin prefix
        if not comp_def and '_' in comp_type:
            base_type = '_'.join(comp_type.split('_')[1:])
            comp_def = next((c for c in self.available_components if c['type'] == base_type), None)
            if not comp_def:
                comp_def = next((c for c in self.available_components if base_type.endswith(c['type'])), None)
        
        dialog = ComponentEditorDialog(
            page=self.page,
            component=comp,
            component_def=comp_def,
            expression_helper=self.expression_helper,
            on_save=lambda: (self._push_history(), self._edit_page(page_idx)),
            on_close=lambda: self._edit_page(page_idx),
        )
        dialog.show()
    
    def _save_config(self, e):
        """Save config to YAML file."""
        if not self.config_path:
            self._set_status("No config file loaded", "orange")
            return
        
        self.current_config['name'] = self.title_field.value
        self.current_config['theme'] = self.theme_dropdown.value
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    self.current_config, f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )
            self._set_status(f"✓ Saved to {self.config_path.name}", "green")
        except Exception as ex:
            self._set_status(f"Error saving: {ex}", "red")
    
    # ============================================================
    # History Management (Undo/Redo)
    # ============================================================
    
    def _push_history(self):
        """Save current config state to history."""
        import copy
        
        # Remove any redo states if we're not at the end
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]
        
        # Add current state
        self._history.append(copy.deepcopy(self.current_config))
        
        # Limit history size
        if len(self._history) > self._max_history:
            self._history.pop(0)
        else:
            self._history_index = len(self._history) - 1
        
        self._update_history_buttons()
    
    def _undo(self, e):
        """Undo last config change."""
        if self._history_index > 0:
            import copy
            self._history_index -= 1
            self.current_config = copy.deepcopy(self._history[self._history_index])
            self._render_pages()
            self._update_history_buttons()
            self._set_status("↩ Undo", "green")
            self.page.update()
    
    def _redo(self, e):
        """Redo previously undone change."""
        if self._history_index < len(self._history) - 1:
            import copy
            self._history_index += 1
            self.current_config = copy.deepcopy(self._history[self._history_index])
            self._render_pages()
            self._update_history_buttons()
            self._set_status("↪ Redo", "green")
            self.page.update()
    
    def _update_history_buttons(self):
        """Update undo/redo button states."""
        self.undo_btn.disabled = self._history_index <= 0
        self.redo_btn.disabled = self._history_index >= len(self._history) - 1
    
    def _preview(self, e):
        """Preview report in browser."""
        if not self.plugin_dropdown.value:
            self._set_status("Please select a plugin", "orange")
            return
        
        if not self.data_dir_field.value:
            self._set_status("Please select a data directory", "orange")
            return
        
        self._save_config(None)
        
        try:
            import tempfile
            output_dir = tempfile.mkdtemp(prefix="bobreview_preview_")
            
            result = cli_wrapper.generate_report(
                plugin_name=self.plugin_dropdown.value,
                data_dir=self.data_dir_field.value,
                output_dir=output_dir,
                dry_run=True,
            )
            
            webbrowser.open(f"file://{result}")
            self._set_status("✓ Preview opened in browser", "green")
            
        except Exception as ex:
            import traceback
            self._show_error_dialog(
                "Preview Error",
                "Failed to generate report preview",
                traceback.format_exc()
            )
    
    def _set_status(self, message: str, color: str):
        """Set status message with color."""
        self.status_text.value = message
        color_map = {
            "green": ft.Colors.GREEN_400,
            "red": ft.Colors.RED_400,
            "orange": ft.Colors.ORANGE_400,
        }
        self.status_text.color = color_map.get(color, ft.Colors.GREY_400)
        self.page.update()
    
    def _show_error_dialog(self, title: str, message: str, details: str = ""):
        """Show error dialog with copy-to-clipboard."""
        details_field = ft.TextField(
            value=details,
            multiline=True,
            read_only=True,
            min_lines=5,
            max_lines=10,
            width=500,
        ) if details else None
        
        def copy_details(e):
            self.page.set_clipboard(details)
            self._set_status("✓ Copied to clipboard", "green")
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        content_controls = [
            ft.Text(message, size=14),
        ]
        if details_field:
            content_controls.extend([
                ft.Container(height=10),
                ft.Text("Details:", weight=ft.FontWeight.BOLD, size=12),
                details_field,
            ])
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400),
                ft.Text(title, color=ft.Colors.RED_400),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(content_controls, spacing=5),
                width=550,
            ),
            actions=[
                ft.TextButton("Copy Details", on_click=copy_details) if details else None,
                ft.ElevatedButton("Close", on_click=close_dialog),
            ],
        )
        # Filter None actions
        dialog.actions = [a for a in dialog.actions if a]
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

