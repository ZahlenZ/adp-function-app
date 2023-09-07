import os
import re

from src.ADPOpenConnection import main
from src.Parameters import main as get_parameters


def test_main_integration():
    """Test that adpOpenConnection calls the ADP API and succesfully retrieves the 200 status and the bearer token."""

    token_regex = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    parameters = get_parameters("mock_input")
    result = main(parameters)

    assert result["status"] == 200
    assert re.match(token_regex, result["bearer_token"])
