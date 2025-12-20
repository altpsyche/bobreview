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
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="LLM",
            ),
        ],
        on_change=lambda e: _handle_nav(e, show_dashboard, show_plugin_list, show_generate, show_llm_settings),
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


def _handle_nav(e, show_dashboard, show_plugin_list, show_generate, show_llm_settings):
    """Handle navigation rail selection."""
    if e.control.selected_index == 0:
        show_dashboard()
    elif e.control.selected_index == 1:
        show_plugin_list()
    elif e.control.selected_index == 2:
        show_generate()
    elif e.control.selected_index == 3:
        show_llm_settings()


def _build_dashboard(page: ft.Page, show_plugins, show_generate, show_llm):
    """Build the dashboard/home view."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=40),
                ft.Text("BobReview", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(
                    "Plugin-First Report Framework",
                    size=18,
                    color=ft.Colors.GREY_400,
                ),
                ft.Container(height=40),
                ft.Row(
                    [
                        _action_card(
                            "Plugins",
                            "Manage and create plugins",
                            ft.Icons.EXTENSION,
                            show_plugins,
                        ),
                        _action_card(
                            "Generate Report",
                            "Run a plugin to generate reports",
                            ft.Icons.PLAY_CIRCLE,
                            show_generate,
                        ),
                        _action_card(
                            "LLM Settings",
                            "Configure API keys",
                            ft.Icons.SETTINGS,
                            show_llm,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    wrap=True,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
        padding=40,
    )


def _action_card(title: str, subtitle: str, icon, on_click):
    """Build an action card for the dashboard."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, size=48, color=ft.Colors.BLUE_300),
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(subtitle, size=14, color=ft.Colors.GREY_300),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        width=220,
        height=180,
        padding=20,
        border_radius=12,
        bgcolor="#1e2632",  # Dark blue-grey for contrast
        border=ft.border.all(1, ft.Colors.BLUE_700),
        on_click=on_click,
        ink=True,
    )


if __name__ == "__main__":
    run_app()

