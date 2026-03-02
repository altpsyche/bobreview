"""
BobReview GUI - Main entry point.

Launches the Flet application with navigation and views.
"""

import flet as ft
from pathlib import Path


def run_app():
    """Launch the BobReview GUI application."""
    ft.app(target=main)


def main(page: ft.Page):
    """Main Flet application."""
    # Configure page
    page.title = "BobReview"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window.width = 1200
    page.window.height = 800
    
    # Import views here to avoid circular imports
    from .views.plugin_list import PluginListView
    from .views.plugin_create import PluginCreateView
    from .views.generate import GenerateView
    from .views.llm_settings import LLMSettingsView
    from .views.config_editor import ConfigEditorView
    
    # Current view content
    content = ft.Container(expand=True)
    
    def show_plugin_list(e=None):
        content.content = PluginListView(page, on_create=show_plugin_create)
        page.update()
    
    def show_plugin_create(e=None):
        content.content = PluginCreateView(page, on_back=show_plugin_list)
        page.update()
    
    def show_generate(e=None):
        content.content = GenerateView(page)
        page.update()
    
    def show_llm_settings(e=None):
        content.content = LLMSettingsView(page)
        page.update()
    
    def show_config_editor(e=None):
        view = ConfigEditorView(page)
        content.content = view
        view.on_mount()
        page.update()
    
    def show_dashboard(e=None):
        content.content = _build_dashboard(page, show_plugin_list, show_generate, show_llm_settings)
        page.update()
    
    # Navigation rail
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="Home",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.EXTENSION_OUTLINED,
                selected_icon=ft.Icons.EXTENSION,
                label="Plugins",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PLAY_CIRCLE_OUTLINED,
                selected_icon=ft.Icons.PLAY_CIRCLE,
                label="Generate",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.EDIT_NOTE_OUTLINED,
                selected_icon=ft.Icons.EDIT_NOTE,
                label="Editor",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="LLM",
            ),
        ],
        on_change=lambda e: _handle_nav(e, show_dashboard, show_plugin_list, show_generate, show_config_editor, show_llm_settings),
    )
    
    # Layout
    page.add(
        ft.Row(
            [
                nav_rail,
                ft.VerticalDivider(width=1),
                content,
            ],
            expand=True,
        )
    )
    
    # Show dashboard initially
    show_dashboard()


def _handle_nav(e, show_dashboard, show_plugin_list, show_generate, show_config_editor, show_llm_settings):
    """Handle navigation rail selection."""
    if e.control.selected_index == 0:
        show_dashboard()
    elif e.control.selected_index == 1:
        show_plugin_list()
    elif e.control.selected_index == 2:
        show_generate()
    elif e.control.selected_index == 3:
        show_config_editor()
    elif e.control.selected_index == 4:
        show_llm_settings()


def _build_dashboard(page: ft.Page, show_plugins, show_generate, show_llm):
    """Build the dashboard/home view."""
    # Get plugin count
    try:
        from .services import cli_wrapper
        plugin_count = len(cli_wrapper.list_plugins())
    except Exception:
        plugin_count = 0
    
    # Get version info from package
    from bobreview import __version__, __description__, __author__
    
    return ft.Container(
        content=ft.Column(
            [
                # Header with gradient effect
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.INSIGHTS, size=56, color=ft.Colors.BLUE_200),
                            ft.Column([
                                ft.Text("BobReview", size=42, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text(f"v{__version__}", size=14, color=ft.Colors.BLUE_200),
                            ], spacing=0),
                        ], spacing=15),
                        ft.Container(height=10),
                        ft.Text(
                            __description__,
                            size=18,
                            color=ft.Colors.GREY_300,
                            weight=ft.FontWeight.W_300,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30,
                    border_radius=16,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1),
                        end=ft.Alignment(1, 1),
                        colors=["#1a237e", "#0d47a1", "#1565c0"],
                    ),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_900),
                        offset=ft.Offset(0, 4),
                    ),
                    width=600,
                ),
                ft.Container(height=30),
                
                # Stats row
                ft.Row([
                    _stat_chip(f"{plugin_count}", "Plugins", ft.Icons.EXTENSION),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                
                ft.Container(height=30),
                
                # Quick actions
                ft.Text("Quick Actions", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                ft.Container(height=15),
                ft.Row(
                    [
                        _action_card(
                            "Plugins",
                            "Create & manage plugins",
                            ft.Icons.EXTENSION,
                            show_plugins,
                            ft.Colors.PURPLE_700,
                        ),
                        _action_card(
                            "Generate",
                            "Create reports from data",
                            ft.Icons.PLAY_CIRCLE,
                            show_generate,
                            ft.Colors.GREEN_700,
                        ),
                        _action_card(
                            "LLM Settings",
                            "Configure AI providers",
                            ft.Icons.SMART_TOY,
                            show_llm,
                            ft.Colors.ORANGE_700,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    wrap=True,
                ),
                
                # Footer with author
                ft.Container(expand=True),  # Spacer
                ft.Text(
                    f"Made by {__author__}",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
        padding=40,
    )


def _stat_chip(value: str, label: str, icon):
    """Build a stat chip."""
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=20, color=ft.Colors.BLUE_300),
            ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text(label, size=14, color=ft.Colors.GREY_400),
        ], spacing=8),
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        border_radius=30,
        bgcolor="#1e2632",
    )


def _action_card(title: str, subtitle: str, icon, on_click, accent_color):
    """Build an action card for the dashboard."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(icon, size=32, color=ft.Colors.WHITE),
                    padding=12,
                    border_radius=12,
                    bgcolor=accent_color,
                ),
                ft.Container(height=10),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(subtitle, size=13, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        ),
        width=180,
        height=180,
        padding=20,
        border_radius=16,
        bgcolor="#1e2632",
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
        on_click=on_click,
        on_hover=lambda e: _card_hover(e),
        ink=True,
    )


def _card_hover(e):
    """Handle card hover effect."""
    e.control.bgcolor = "#252f3d" if e.data == "true" else "#1e2632"
    e.control.update()


if __name__ == "__main__":
    run_app()

