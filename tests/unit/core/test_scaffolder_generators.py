"""
Unit tests for scaffolder generator modules.

Tests that generated code contains expected patterns and structures.
"""

import pytest

from bobreview.core.plugin_system.scaffolder.generators import (
    generate_plugin_py,
    generate_csv_parser,
    generate_context_builder,
    generate_executor,
    generate_chart_generator,
    generate_analysis_module,
    generate_theme_module,
    generate_widgets_module,
    generate_component_module,
    generate_manifest,
    generate_report_system,
    generate_user_report_config,
)


class TestGeneratePluginPy:
    """Tests for plugin.py generator."""

    def test_has_class_definition(self):
        """Generated code should contain plugin class definition."""
        content = generate_plugin_py("test-plugin", "test_plugin", "TestPlugin", "full")
        assert "class TestPluginPlugin(BasePlugin):" in content

    def test_has_on_load_method(self):
        """Generated code should have on_load method."""
        content = generate_plugin_py("test-plugin", "test_plugin", "TestPlugin", "full")
        assert "def on_load(self, registry)" in content

    def test_full_template_has_helper(self):
        """Full template should use PluginHelper."""
        content = generate_plugin_py("test-plugin", "test_plugin", "TestPlugin", "full")
        assert "PluginHelper(registry, self.name)" in content

    def test_has_lifecycle_hooks(self):
        """Generated code should have lifecycle hooks."""
        content = generate_plugin_py("test-plugin", "test_plugin", "TestPlugin", "full")
        assert "def on_report_start" in content
        assert "def on_report_complete" in content

    def test_minimal_template(self):
        """Minimal template should still have core structure."""
        content = generate_plugin_py("test-plugin", "test_plugin", "TestPlugin", "minimal")
        assert "class TestPluginPlugin(BasePlugin):" in content
        assert "def on_load" in content


class TestGenerateCsvParser:
    """Tests for CSV parser generator."""

    def test_has_parser_class(self):
        """Generated code should contain parser class."""
        content = generate_csv_parser("test-plugin", "TestPlugin")
        assert "class TestPluginCsvParser:" in content

    def test_has_parse_directory_method(self):
        """Generated code should have parse_directory method."""
        content = generate_csv_parser("test-plugin", "TestPlugin")
        assert "def parse_directory(self, directory: Path)" in content

    def test_has_schema_loading(self):
        """Generated code should load schema from YAML."""
        content = generate_csv_parser("test-plugin", "TestPlugin")
        assert "data_schema.yaml" in content
        assert "load_schema" in content

    def test_has_type_conversion(self):
        """Generated code should handle type conversion."""
        content = generate_csv_parser("test-plugin", "TestPlugin")
        assert "convert_value" in content
        assert "field_type" in content


class TestGenerateContextBuilder:
    """Tests for context builder generator."""

    def test_has_context_builder_class(self):
        """Generated code should contain context builder class."""
        content = generate_context_builder("test-plugin", "TestPlugin")
        assert "class TestPluginContextBuilder:" in content

    def test_has_build_context_method(self):
        """Generated code should have build_context method."""
        content = generate_context_builder("test-plugin", "TestPlugin")
        assert "def build_context(" in content

    def test_has_dataframe_normalization(self):
        """Generated code should handle DataFrame normalization."""
        content = generate_context_builder("test-plugin", "TestPlugin")
        assert "_normalize_data_to_list" in content


class TestGenerateExecutor:
    """Tests for executor generator."""

    def test_has_generate_report_function(self):
        """Generated code should have generate_report function."""
        content = generate_executor("test-plugin", "test_plugin", "TestPlugin")
        assert "def generate_report(" in content

    def test_has_theme_mapping(self):
        """Generated code should have THEMES mapping."""
        content = generate_executor("test-plugin", "test_plugin", "TestPlugin")
        assert "THEMES = {" in content
        assert "midnight" in content.lower()

    def test_has_llm_content_generation(self):
        """Generated code should have LLM content generation."""
        content = generate_executor("test-plugin", "test_plugin", "TestPlugin")
        assert "generate_llm_content" in content
        assert "dry_run" in content

    def test_has_component_renderer(self):
        """Generated code should have ComponentRenderer class."""
        content = generate_executor("test-plugin", "test_plugin", "TestPlugin")
        assert "class ComponentRenderer:" in content

    def test_has_template_loader(self):
        """Generated code should have TemplateLoader class."""
        content = generate_executor("test-plugin", "test_plugin", "TestPlugin")
        assert "class TemplateLoader:" in content


class TestGenerateChartGenerator:
    """Tests for chart generator."""

    def test_has_chart_generator_class(self):
        """Generated code should have chart generator class."""
        content = generate_chart_generator("test-plugin", "TestPlugin")
        assert "class TestPluginChartGenerator:" in content

    def test_has_generate_chart_method(self):
        """Generated code should have generate_chart method."""
        content = generate_chart_generator("test-plugin", "TestPlugin")
        assert "def generate_chart(" in content

    def test_supports_multiple_chart_types(self):
        """Generated code should support multiple chart types."""
        content = generate_chart_generator("test-plugin", "TestPlugin")
        assert "histogram" in content
        assert "pie" in content or "doughnut" in content
        assert "line" in content
        assert "bar" in content

    def test_has_hex_to_rgba(self):
        """Generated code should have color conversion."""
        content = generate_chart_generator("test-plugin", "TestPlugin")
        assert "_hex_to_rgba" in content


class TestGenerateThemeModule:
    """Tests for theme module generator."""

    def test_has_four_themes(self):
        """Generated code should have 4 themes."""
        content = generate_theme_module("test-plugin", "test_plugin", "TestPlugin")
        assert "TEST_PLUGIN_MIDNIGHT" in content
        assert "TEST_PLUGIN_AURORA" in content
        assert "TEST_PLUGIN_SUNSET" in content
        assert "TEST_PLUGIN_FROST" in content

    def test_has_report_theme_dataclass(self):
        """Generated code should have ReportTheme dataclass."""
        content = generate_theme_module("test-plugin", "test_plugin", "TestPlugin")
        assert "@dataclass" in content
        assert "class ReportTheme:" in content

    def test_has_css_generation(self):
        """Generated code should have CSS generation function."""
        content = generate_theme_module("test-plugin", "test_plugin", "TestPlugin")
        assert "get_theme_css_variables" in content
        assert ":root {" in content

    def test_themes_have_required_fields(self):
        """Themes should have color and font fields."""
        content = generate_theme_module("test-plugin", "test_plugin", "TestPlugin")
        assert "accent=" in content
        assert "bg=" in content
        assert "text_main=" in content
        assert "font_family=" in content


class TestGenerateAnalysisModule:
    """Tests for analysis module generator."""

    def test_has_analyze_function(self):
        """Generated code should have analyze function."""
        content = generate_analysis_module("test-plugin", "test_plugin")
        assert "def analyze_test_plugin_data(" in content

    def test_has_statistics(self):
        """Generated code should calculate statistics."""
        content = generate_analysis_module("test-plugin", "test_plugin")
        assert "statistics" in content
        assert "mean" in content
        assert "median" in content


class TestGenerateWidgetsModule:
    """Tests for widgets module generator."""

    def test_has_stat_card_class(self):
        """Generated code should have stat card widget."""
        content = generate_widgets_module("test-plugin", "test_plugin", "TestPlugin")
        assert "class TestPluginStatCard:" in content

    def test_has_render_method(self):
        """Generated code should have render method."""
        content = generate_widgets_module("test-plugin", "test_plugin", "TestPlugin")
        assert "def render(" in content

    def test_has_css_method(self):
        """Generated code should have get_css method."""
        content = generate_widgets_module("test-plugin", "test_plugin", "TestPlugin")
        assert "def get_css(" in content


class TestGenerateComponentModule:
    """Tests for component module generator."""

    def test_has_chart_component(self):
        """Generated code should have chart component."""
        content = generate_component_module("test-plugin", "test_plugin", "TestPlugin")
        assert "class TestPluginChartComponent:" in content

    def test_has_register_decorator(self):
        """Generated code should use register_component decorator."""
        content = generate_component_module("test-plugin", "test_plugin", "TestPlugin")
        assert "@register_component(" in content

    def test_has_proptypes(self):
        """Generated code should use PropTypes."""
        content = generate_component_module("test-plugin", "test_plugin", "TestPlugin")
        assert "PropTypes.string" in content
        assert "PropTypes.boolean" in content


class TestGenerateManifest:
    """Tests for manifest.json generator."""

    def test_has_required_fields(self):
        """Generated manifest should have required fields."""
        manifest = generate_manifest("test-plugin", "test_plugin", "TestPlugin", "full")
        assert manifest["name"] == "test-plugin"
        assert "version" in manifest
        assert "entry_point" in manifest

    def test_full_template_has_all_provides(self):
        """Full template should provide all component types."""
        manifest = generate_manifest("test-plugin", "test_plugin", "TestPlugin", "full")
        provides = manifest["provides"]
        assert "report_systems" in provides
        assert "data_parsers" in provides
        assert "context_builders" in provides
        assert "chart_generators" in provides


class TestGenerateReportSystem:
    """Tests for report_system.json generator."""

    def test_has_schema_version(self):
        """Generated report system should have schema version."""
        system = generate_report_system("test-plugin", "test_plugin")
        assert "schema_version" in system

    def test_has_data_source(self):
        """Generated report system should have data source config."""
        system = generate_report_system("test-plugin", "test_plugin")
        assert "data_source" in system
        assert "fields" in system["data_source"]

    def test_respects_theme(self):
        """Generated report system should use provided theme."""
        system = generate_report_system("test-plugin", "test_plugin", "aurora")
        assert system["theme"] == "aurora"


class TestGenerateUserReportConfig:
    """Tests for report_config.yaml generator."""

    def test_is_valid_yaml_structure(self):
        """Generated config should be valid YAML structure."""
        content = generate_user_report_config("test-plugin", "test_plugin")
        assert "pages:" in content
        assert "components:" in content

    def test_has_multiple_pages(self):
        """Generated config should define multiple pages."""
        content = generate_user_report_config("test-plugin", "test_plugin")
        assert "id: tavern" in content
        assert "id: armoury" in content
        assert "id: quests" in content
        assert "id: registry" in content

    def test_has_component_reference(self):
        """Generated config should have component reference section."""
        content = generate_user_report_config("test-plugin", "test_plugin")
        assert "COMPONENT REFERENCE" in content
