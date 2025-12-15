"""
Configuration for BobReview.

Single unified Config class - the only config you need.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..services.llm.providers.factory import list_providers


@dataclass
class Config:
    """
    Unified configuration for report generation.
    
    All settings in one place. No merging needed.
    """
    # Report metadata
    title: str = ""
    
    # LLM settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_api_key: Optional[str] = None
    llm_api_key_env: Optional[str] = None  # Environment variable name for API key
    llm_api_base: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_chunk_size: int = 10
    llm_combine_warning_threshold: int = 100000  # Character threshold for combine warning
    
    # Theme and output
    theme: str = "dark"
    output_dir: str = "./output"
    output_filename: str = "report.html"
    embed_images: bool = True
    linked_css: bool = False
    
    # Execution
    verbose: bool = False
    quiet: bool = False
    dry_run: bool = False
    sample_size: Optional[int] = None
    
    # Cache
    use_cache: bool = True
    cache_dir: Path = field(default_factory=lambda: Path(".bobreview_cache"))
    
    # Thresholds (plugin-specific, stored as dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    
    # Plugin extensions (from JSON + YAML override)
    extensions: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate config. Returns list of errors."""
        errors = []
        if self.llm_temperature < 0 or self.llm_temperature > 2:
            errors.append("llm_temperature must be 0-2")
        if self.llm_max_tokens <= 0:
            errors.append("llm_max_tokens must be > 0")
        if self.llm_provider not in list_providers():
            errors.append(f"Invalid llm_provider: {self.llm_provider}")
        if self.output_dir and not isinstance(self.output_dir, (str, Path)):
            errors.append("output_dir must be a string or Path")
        if self.theme and not isinstance(self.theme, str):
            errors.append("theme must be a string")
        if self.cache_dir and not isinstance(self.cache_dir, Path):
            errors.append("cache_dir must be a Path")
        return errors


def load_config(
    cli_args: Optional[Dict[str, Any]] = None,
    yaml_path: Optional[Path] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> Config:
    """
    Load config with precedence: CLI > YAML > JSON > Defaults.
    
    This is the ONE place config is resolved.
    """
    config = Config()
    
    # Apply JSON defaults (plugin) - ALL FLAT FORMAT
    if json_data:
        if json_data.get('llm_provider'):
            config.llm_provider = json_data['llm_provider']
        if json_data.get('llm_model'):
            config.llm_model = json_data['llm_model']
        if json_data.get('llm_temperature') is not None:
            config.llm_temperature = json_data['llm_temperature']
        if json_data.get('llm_max_tokens'):
            config.llm_max_tokens = json_data['llm_max_tokens']
        
        if json_data.get('theme'):
            config.theme = json_data['theme']
        
        if json_data.get('extensions'):
            config.extensions = json_data['extensions'].copy()
    
    # Apply YAML user config
    if yaml_path and yaml_path.exists():
        import yaml as yaml_lib
        with open(yaml_path) as f:
            yaml_data = yaml_lib.safe_load(f) or {}
        
        if yaml_data.get('theme'):
            config.theme = yaml_data['theme']
        if yaml_data.get('output_dir'):
            config.output_dir = yaml_data['output_dir']
        
        # YAML config overrides JSON extensions
        if yaml_data.get('config'):
            for key, value in yaml_data['config'].items():
                if isinstance(value, dict) and key in config.extensions:
                    config.extensions[key] = {**config.extensions[key], **value}
                else:
                    config.extensions[key] = value
    
    # Apply CLI args (highest priority)
    if cli_args:
        if cli_args.get('theme'):
            config.theme = cli_args['theme']
        if cli_args.get('output'):
            config.output_dir = cli_args['output']
        if cli_args.get('verbose'):
            config.verbose = True
        if cli_args.get('quiet'):
            config.quiet = True
        if cli_args.get('dry_run'):
            config.dry_run = True
        if cli_args.get('sample'):
            config.sample_size = cli_args['sample']
        if cli_args.get('llm_provider'):
            config.llm_provider = cli_args['llm_provider']
        if cli_args.get('llm_model'):
            config.llm_model = cli_args['llm_model']
        if cli_args.get('llm_api_key'):
            config.llm_api_key = cli_args['llm_api_key']
    
    return config
