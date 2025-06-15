import json
from pathlib import Path
from typing import Dict, Optional

from .context import Context
from .models import Feature


class Composer:
    """Class responsible for composing different features into a final configuration."""
    
    def __init__(self, context: Context):
        self.context = context
        self.config: Dict = {}
    
    def compose(self) -> Dict:
        """Compose all features into a final configuration."""
        feature_order = ["workspace", "runtime", "expose", "container"]
        for feature_name in feature_order:
            if feature_name in self.context.features:
                feature = self.context.features[feature_name]
                self._add_feature(feature)
        return self.config
    
    def _add_feature(self, feature: Feature) -> None:
        """Add a feature to the configuration."""
        feature_dict = feature.compose()
        for key, value in feature_dict.items():
            if key in self.config and isinstance(self.config[key], dict):
                self.config[key].update(value)
            elif key in self.config and isinstance(self.config[key], list):
                self.config[key].extend(value)
            else:
                self.config[key] = value
    
    def save(self, output_path: Optional[Path] = None) -> None:
        """Save the composed configuration to a file."""
        if self.context.dry_run:
            print(json.dumps(self.config, indent=2))
            return
            
        output_path = output_path or self.context.output
        if not output_path:
            raise ValueError("No output path specified")
            
        with open(output_path, 'w') as f:
            json.dump(self.config, f, indent=2)