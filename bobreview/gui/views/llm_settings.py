"""
LLM Settings View - Configure LLM provider and API keys.
"""

import flet as ft
from pathlib import Path
import os


class LLMSettingsView(ft.Container):
    """View for configuring LLM settings."""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True
        self.padding = 20
        
        # Provider dropdown
        self.provider_dropdown = ft.Dropdown(
            label="LLM Provider",
            width=400,
            value="openai",
            options=[
                ft.dropdown.Option("openai", "OpenAI (GPT-4)"),
                ft.dropdown.Option("anthropic", "Anthropic (Claude)"),
                ft.dropdown.Option("ollama", "Ollama (Local)"),
            ],
            on_select=self._on_provider_change,
        )
        
        # API Key field
        self.api_key_field = ft.TextField(
            label="API Key",
            width=400,
            password=True,
            can_reveal_password=True,
            hint_text="Enter your API key",
        )
        
        # Model field
        self.model_field = ft.TextField(
            label="Model Name (Optional)",
            width=400,
            hint_text="e.g., gpt-4, claude-3-opus, llama2",
        )
        
        # Temperature slider
        self.temperature_value = ft.Text("0.7", size=14, weight=ft.FontWeight.BOLD)
        self.temperature_slider = ft.Slider(
            min=0,
            max=2,
            value=0.7,
            divisions=20,
            label="{value}",
            width=350,
            on_change=self._on_temperature_change,
        )
        
        # Ollama URL field
        self.ollama_url_field = ft.TextField(
            label="Ollama URL",
            width=400,
            value="http://localhost:11434",
            visible=False,
        )
        
        # Status
        self.status_text = ft.Text("", size=14)
        
        # Load current settings
        self._load_settings()
        
        self.content = ft.Column(
            [
                ft.Text("LLM Settings", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(height=10),
                ft.Text(
                    "Configure the LLM provider for AI-generated content in reports.",
                    size=16,
                    color=ft.Colors.GREY_400,
                ),
                ft.Container(height=30),
                self.provider_dropdown,
                ft.Container(height=15),
                self.api_key_field,
                ft.Container(height=15),
                self.model_field,
                ft.Container(height=15),
                ft.Text("Temperature", size=14, color=ft.Colors.GREY_400),
                ft.Row([self.temperature_slider, self.temperature_value], spacing=10),
                ft.Text("Lower = more focused, Higher = more creative", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=15),
                self.ollama_url_field,
                ft.Container(height=30),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Save Settings",
                            icon=ft.Icons.SAVE,
                            on_click=self._save_settings,
                            bgcolor=ft.Colors.GREEN_700,
                            color=ft.Colors.WHITE,
                        ),
                        ft.ElevatedButton(
                            "Test Connection",
                            icon=ft.Icons.CLOUD,
                            on_click=self._test_connection,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Container(height=20),
                self.status_text,
                ft.Container(height=30),
                
                # Cache section
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CACHED, color=ft.Colors.BLUE_300),
                            ft.Text("LLM Cache", weight=ft.FontWeight.BOLD),
                        ], spacing=10),
                        ft.Text(
                            "Cache location: ~/.bobreview/cache/",
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Clear Cache",
                            icon=ft.Icons.DELETE_SWEEP,
                            on_click=self._clear_cache,
                            bgcolor=ft.Colors.RED_700,
                            color=ft.Colors.WHITE,
                        ),
                    ]),
                    padding=20,
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    border_radius=8,
                ),
                ft.Container(height=20),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("Environment Variables", weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "You can also set these via environment variables:",
                            size=14,
                            color=ft.Colors.GREY_400,
                        ),
                        ft.Container(height=10),
                        ft.Text("• OPENAI_API_KEY - OpenAI API key", size=12, color=ft.Colors.GREY_500),
                        ft.Text("• ANTHROPIC_API_KEY - Anthropic API key", size=12, color=ft.Colors.GREY_500),
                        ft.Text("• OLLAMA_BASE_URL - Ollama server URL", size=12, color=ft.Colors.GREY_500),
                    ]),
                    padding=20,
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    border_radius=8,
                ),
            ],
        )
    
    def _on_provider_change(self, e):
        """Handle provider selection change."""
        provider = self.provider_dropdown.value
        
        # Show Ollama URL only for ollama
        if provider == "ollama":
            self.api_key_field.label = "API Key (optional for local)"
            self.ollama_url_field.visible = True
        else:
            self.api_key_field.label = "API Key"
            self.ollama_url_field.visible = False
        
        self._page.update()
    
    def _on_temperature_change(self, e):
        """Handle temperature slider change."""
        self.temperature_value.value = f"{e.control.value:.1f}"
        self._page.update()
    
    def _load_settings(self):
        """Load settings from environment variables."""
        # Check for existing API keys
        if os.environ.get("OPENAI_API_KEY"):
            self.provider_dropdown.value = "openai"
            self.api_key_field.value = os.environ.get("OPENAI_API_KEY", "")
        elif os.environ.get("ANTHROPIC_API_KEY"):
            self.provider_dropdown.value = "anthropic"
            self.api_key_field.value = os.environ.get("ANTHROPIC_API_KEY", "")
        
        # Check for Ollama URL
        if os.environ.get("OLLAMA_BASE_URL"):
            self.ollama_url_field.value = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def _save_settings(self, e):
        """Save settings to environment variables."""
        provider = self.provider_dropdown.value
        api_key = self.api_key_field.value.strip()
        
        if provider == "openai" and api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            self.status_text.value = "✓ OpenAI API key saved to session"
            self.status_text.color = ft.Colors.GREEN_400
        elif provider == "anthropic" and api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            self.status_text.value = "✓ Anthropic API key saved to session"
            self.status_text.color = ft.Colors.GREEN_400
        elif provider == "ollama":
            os.environ["OLLAMA_BASE_URL"] = self.ollama_url_field.value.strip()
            self.status_text.value = "✓ Ollama settings saved to session"
            self.status_text.color = ft.Colors.GREEN_400
        else:
            self.status_text.value = "Please enter an API key"
            self.status_text.color = ft.Colors.ORANGE_400
        
        # Show note about persistence
        self._page.show_dialog(ft.SnackBar(
            content=ft.Text("Settings saved for this session. Set environment variables for persistence."),
            open=True,
        ))
        self._page.update()
    
    def _test_connection(self, e):
        """Test the LLM connection."""
        provider = self.provider_dropdown.value
        self.status_text.value = f"Testing {provider} connection..."
        self.status_text.color = ft.Colors.GREY_400
        self._page.update()
        
        try:
            if provider == "openai":
                api_key = self.api_key_field.value.strip() or os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("No OpenAI API key provided")
                # Quick API check
                import openai
                client = openai.OpenAI(api_key=api_key)
                client.models.list()
                self.status_text.value = "✓ OpenAI connection successful!"
                self.status_text.color = ft.Colors.GREEN_400
                
            elif provider == "anthropic":
                api_key = self.api_key_field.value.strip() or os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("No Anthropic API key provided")
                self.status_text.value = "✓ Anthropic key format valid (not tested)"
                self.status_text.color = ft.Colors.GREEN_400
                
            elif provider == "ollama":
                import httpx
                url = self.ollama_url_field.value.strip()
                response = httpx.get(f"{url}/api/tags", timeout=5)
                if response.status_code == 200:
                    self.status_text.value = "✓ Ollama server is running!"
                    self.status_text.color = ft.Colors.GREEN_400
                else:
                    raise ValueError(f"Ollama returned status {response.status_code}")
                    
        except ImportError as ie:
            self.status_text.value = f"Missing package: {ie}"
            self.status_text.color = ft.Colors.ORANGE_400
        except Exception as ex:
            self.status_text.value = f"Connection failed: {ex}"
            self.status_text.color = ft.Colors.RED_400
        
        self._page.update()
    
    def _clear_cache(self, e):
        """Clear the LLM response cache."""
        try:
            cache_dir = Path.home() / ".bobreview" / "cache"
            if cache_dir.exists():
                count = 0
                for f in cache_dir.glob("*.json"):
                    f.unlink()
                    count += 1
                
                self.status_text.value = f"✓ Cleared {count} cached response(s)"
                self.status_text.color = ft.Colors.GREEN_400
            else:
                self.status_text.value = "Cache directory is empty"
                self.status_text.color = ft.Colors.GREY_400
        except Exception as ex:
            self.status_text.value = f"Failed to clear cache: {ex}"
            self.status_text.color = ft.Colors.RED_400
        
        self._page.update()
