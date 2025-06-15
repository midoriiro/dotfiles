import pytest

from devcc.models import Feature


class TestFeature(Feature):
    """Concrete implementation of Feature for testing purposes."""
    pass

def test_feature_compose_not_implemented():
    """Test that calling compose() on the base Feature class raises NotImplementedError."""
    feature = TestFeature()
    with pytest.raises(NotImplementedError, match="Subclasses must implement this method"):
        feature.compose() 