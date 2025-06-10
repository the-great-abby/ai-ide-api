import pytest
from unittest.mock import patch, mock_open, MagicMock
from scripts import onboarding_path_optimizer

def test_onboarding_path_optimizer(tmp_path):
    docs_content = "# ONBOARDING\nSome onboarding doc."
    feedback_content = "# FEEDBACK\nSome feedback."
    suggestions = "1. Clarify step 1.\n2. Add a new path."
    output_file = tmp_path / "onboarding_optimization_suggestions.md"
    with patch("scripts.onboarding_path_optimizer.read_files", side_effect=[docs_content, feedback_content]), \
         patch("scripts.onboarding_path_optimizer.call_ollama", return_value=suggestions), \
         patch("builtins.open", mock_open()) as m_open, \
         patch.object(onboarding_path_optimizer, "logger") as mock_logger, \
         patch("argparse.ArgumentParser.parse_args", return_value=type("Args", (), {"dry_run": False})()):
        onboarding_path_optimizer.main()
        log_msgs = " ".join(str(call) for call in mock_logger.info.call_args_list)
        assert "LLM SUGGESTIONS" in log_msgs
        assert "CREATED" in log_msgs 