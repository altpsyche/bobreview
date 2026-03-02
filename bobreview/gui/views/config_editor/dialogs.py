"""
Dialogs - Page and Component editor dialogs.

Encapsulates the dialog creation logic for editing pages and components.
"""

import flet as ft
from typing import Dict, Any, List, Callable, Optional
from .expression_helper import ExpressionHelper


class PageEditorDialog:
    """Dialog for editing a page's properties and components."""
    
    def __init__(
        self,
        page: ft.Page,
        page_data: dict,
        page_index: int,
        available_components: List[dict],
        on_save: Callable,
        on_edit_component: Callable[[int], None],
    ):
        self.ft_page = page
        self.page_data = page_data
        self.page_index = page_index
        self.available_components = available_components
        self.on_save = on_save
        self.on_edit_component = on_edit_component
        self.dialog: Optional[ft.AlertDialog] = None
        
        # Create form fields
        self.id_field = ft.TextField(
            label="Page ID",
            value=page_data.get('id', ''),
            width=200,
        )
        self.title_field = ft.TextField(
            label="Title",
            value=page_data.get('title', ''),
            width=300,
        )
        self.icon_field = ft.TextField(
            label="Icon (FontAwesome)",
            value=page_data.get('icon', ''),
            width=200,
        )
        self.layout_dropdown = ft.Dropdown(
            label="Layout",
            width=200,
            value=page_data.get('layout', 'single-column'),
            options=[
                ft.dropdown.Option("single-column", "Single Column"),
                ft.dropdown.Option("two-column", "Two Column"),
            ],
        )
        
        # Component type dropdown
        self.comp_dropdown = ft.Dropdown(
            label="Add Component",
            width=250,
            options=[
                ft.dropdown.Option(c['type'], c['label'])
                for c in available_components
            ],
        )
        
        # Components list container
        self.components_column = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
    
    def _render_components(self):
        """Render the components list."""
        self.components_column.controls.clear()
        
        for j, comp in enumerate(self.page_data.get('components', [])):
            comp_type = comp.get('type', 'unknown')
            comp_label = comp_type.split('_')[-1].title()
            comp_title = comp.get('title', '') or comp.get('label', '') or ''
            display = f"{j+1}. {comp_label}"
            if comp_title:
                display += f" - {comp_title[:20]}"
            
            self.components_column.controls.append(
                ft.Row([
                    ft.Text(display, expand=True, size=12),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_size=16,
                        tooltip="Edit component",
                        on_click=lambda e, idx=j: self._on_edit_component(idx),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_size=16,
                        on_click=lambda e, idx=j: self._remove_component(idx),
                    ),
                ])
            )
    
    def _remove_component(self, comp_idx: int):
        """Remove a component."""
        self.page_data.get('components', []).pop(comp_idx)
        self._render_components()
        self.ft_page.update()
    
    def _on_edit_component(self, comp_idx: int):
        """Handle edit component click."""
        self.ft_page.pop_dialog()
        self.on_edit_component(comp_idx)
    
    def _add_component(self, e):
        """Add a new component."""
        if self.comp_dropdown.value:
            self.page_data.setdefault('components', []).append({
                'type': self.comp_dropdown.value,
            })
            self._render_components()
            self.ft_page.update()
    
    def _save_page(self, e):
        """Save page data."""
        self.page_data['id'] = self.id_field.value
        self.page_data['title'] = self.title_field.value
        self.page_data['icon'] = self.icon_field.value
        self.page_data['layout'] = self.layout_dropdown.value
        self.ft_page.pop_dialog()
        self.on_save()
    
    def _close_dialog(self, e):
        """Close dialog without saving."""
        self.ft_page.pop_dialog()

    def show(self):
        """Show the dialog."""
        self._render_components()
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Edit Page: {self.page_data.get('title', 'Untitled')}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([self.id_field, self.title_field]),
                    ft.Row([self.icon_field, self.layout_dropdown]),
                    ft.Divider(height=20),
                    ft.Text("Components:", weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.components_column,
                        height=200,
                        border=ft.border.all(1, ft.Colors.GREY_800),
                        border_radius=4,
                        padding=10,
                    ),
                    ft.Row([
                        self.comp_dropdown,
                        ft.IconButton(icon=ft.Icons.ADD, on_click=self._add_component),
                    ]),
                ], spacing=10),
                width=600,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._close_dialog),
                ft.ElevatedButton("Save", on_click=self._save_page),
            ],
        )
        
        self.ft_page.show_dialog(self.dialog)


class ComponentEditorDialog:
    """Dialog for editing a component's properties."""
    
    def __init__(
        self,
        page: ft.Page,
        component: dict,
        component_def: Optional[dict],
        expression_helper: ExpressionHelper,
        on_save: Callable,
        on_close: Callable,
    ):
        self.ft_page = page
        self.component = component
        self.component_def = component_def
        self.expression_helper = expression_helper
        self.on_save = on_save
        self.on_close = on_close
        self.dialog: Optional[ft.AlertDialog] = None
        self.fields: Dict[str, Any] = {}
    
    def _create_field(self, prop_name: str, prop_config: dict) -> ft.Control:
        """Create appropriate field control based on type."""
        current_value = self.component.get(prop_name, '')
        if isinstance(current_value, list):
            current_value = str(current_value)
        
        field_type = prop_config.get('type', 'text')
        field_label = prop_config.get('label', prop_name.replace('_', ' ').title())
        
        if field_type == 'dropdown':
            options = prop_config.get('options', [])
            return ft.Dropdown(
                label=field_label,
                width=250,
                value=str(current_value) if current_value else (options[0] if options else ''),
                options=[ft.dropdown.Option(opt, opt.title()) for opt in options],
            )
        elif field_type == 'number':
            return ft.TextField(
                label=field_label,
                value=str(current_value) if current_value else '',
                width=150,
                keyboard_type=ft.KeyboardType.NUMBER,
            )
        elif field_type == 'checkbox':
            return ft.Checkbox(
                label=field_label,
                value=bool(current_value) if current_value else False,
            )
        elif field_type == 'multiline':
            return ft.TextField(
                label=field_label,
                value=str(current_value) if current_value else '',
                width=500,
                multiline=True,
                min_lines=5,
                max_lines=15,
            )
        elif field_type == 'list':
            return ft.TextField(
                label=field_label,
                value=str(current_value) if current_value else '',
                width=500,
                hint_text="Enter as YAML list or [item1, item2]",
                multiline=True,
                min_lines=2,
                max_lines=6,
            )
        else:
            return ft.TextField(
                label=field_label,
                value=str(current_value) if current_value else '',
                width=400,
            )
    
    def _build_field_controls(self) -> List[ft.Control]:
        """Build all field controls."""
        controls = []
        props_def = self.component_def.get('props', {}) if self.component_def else {}
        
        # Handle legacy format (list of strings)
        if isinstance(props_def, list):
            props_def = {p: {"type": "text", "label": p.replace('_', ' ').title()} for p in props_def}
        
        expressions = self.expression_helper.get_expressions()
        
        for prop_name, prop_config in props_def.items():
            field = self._create_field(prop_name, prop_config)
            self.fields[prop_name] = field
            
            field_type = prop_config.get('type', 'text')
            
            # Add expression helper for text/multiline fields
            if field_type in ['text', 'multiline']:
                expr_dropdown = ft.Dropdown(
                    label="Insert Data",
                    width=200,
                    options=[ft.dropdown.Option(expr, label) for expr, label in expressions],
                    on_select=lambda e, f=field: (
                        setattr(f, 'value', (f.value or '') + e.data),
                        self.ft_page.update()
                    ),
                )
                controls.append(ft.Row([field, expr_dropdown], spacing=5, wrap=True))
            else:
                controls.append(field)
        
        return controls
    
    def _save_component(self, e):
        """Save component data."""
        import ast

        for prop, field in self.fields.items():
            if isinstance(field, ft.Checkbox):
                value = field.value
            elif isinstance(field, ft.Dropdown):
                value = field.value
            else:
                value = field.value
                if value and value.startswith('[') and value.endswith(']'):
                    try:
                        value = ast.literal_eval(value)
                    except Exception:
                        pass

            if value or value is False:
                self.component[prop] = value
            elif prop in self.component:
                del self.component[prop]

        self.ft_page.pop_dialog()
        self.on_save()

    def _close_dialog(self, e):
        """Close dialog."""
        self.ft_page.pop_dialog()
        self.on_close()
    
    def show(self):
        """Show the dialog."""
        comp_type = self.component.get('type', 'unknown')
        field_controls = self._build_field_controls()
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WIDGETS, color=ft.Colors.BLUE_300),
                ft.Text(f"Edit: {comp_type.split('_')[-1].title()}"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column(field_controls, spacing=10, scroll=ft.ScrollMode.AUTO),
                width=550,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._close_dialog),
                ft.ElevatedButton("Save", on_click=self._save_component),
            ],
        )
        
        self.ft_page.show_dialog(self.dialog)
