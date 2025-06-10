import pytest
from unittest.mock import patch, mock_open, MagicMock
from scripts import user_story_completeness_checker

def test_user_story_completeness_missing(tmp_path):
    # Simulate Makefile and API files with targets/endpoints
    makefile_content = "target1:\ntarget2:\n"
    api_content = "@router.get('/foo')\n@router.post('/bar')\n"
    user_story_dir = tmp_path / "user_stories"
    user_story_dir.mkdir()
    # No user story files exist
    with patch("builtins.open", mock_open(read_data=makefile_content)) as m_open, \
         patch("glob.glob", side_effect=lambda pat: [] if "Makefile.ai-*" in pat else []), \
         patch("pathlib.Path.glob", return_value=[]), \
         patch("os.path.exists", return_value=True), \
         patch("scripts.user_story_completeness_checker.USER_STORY_DIR", str(user_story_dir)), \
         patch("scripts.user_story_completeness_checker.API_FILES", ["api_file.py"]), \
         patch("scripts.user_story_completeness_checker.MAKEFILES", ["Makefile"]), \
         patch("scripts.user_story_completeness_checker.parse_api_endpoints", return_value={"/foo", "/bar"}), \
         patch("scripts.user_story_completeness_checker.parse_makefile_targets", return_value={"target1", "target2"}), \
         patch.object(user_story_completeness_checker, "logger") as mock_logger:
        # Non-dry-run: should create files
        with patch("argparse.ArgumentParser.parse_args", return_value=type("Args", (), {"dry_run": False})()):
            user_story_completeness_checker.main()
        log_msgs = " ".join(str(call) for call in mock_logger.info.call_args_list)
        assert "MISSING" in log_msgs
        assert "CREATED" in log_msgs 