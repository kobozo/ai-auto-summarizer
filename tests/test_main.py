"""Unit tests for the main module."""

from unittest.mock import patch

from ai_auto_summarizer.main import demo_function


def test_demo_function():
    """Test that demo_function returns the value from settings.the_var."""
    with patch("ai_auto_summarizer.main.settings") as mock_settings:
        # Set up the mock
        mock_settings.the_var = "test_value"

        # Call the function
        result = demo_function()

        # Assert the result
        assert result == "test_value"
        # Verify the settings were accessed
        assert mock_settings.the_var == "test_value"
