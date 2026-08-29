import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.cli.client import F9l3CliError
from app.cli.main import build_parser, main, output_result


@pytest.mark.unit
def test_cli_parser_version() -> None:
    """CLI parser correctly parses version subcommand."""
    parser = build_parser()
    args = parser.parse_args(["version", "--json"])
    assert args.command == "version"
    assert args.json is True


@pytest.mark.unit
def test_cli_parser_login() -> None:
    """CLI parser correctly parses login parameters."""
    parser = build_parser()
    args = parser.parse_args(["login", "-u", "alice", "-p", "Secr3t!"])
    assert args.command == "login"
    assert args.username == "alice"
    assert args.password == "Secr3t!"


@pytest.mark.unit
def test_cli_parser_send() -> None:
    """CLI parser correctly parses send parameters."""
    parser = build_parser()
    recipient_id = "11111111-2222-3333-4444-555555555555"
    args = parser.parse_args(["send", "-f", "payload.bin", "-r", recipient_id])
    assert args.command == "send"
    assert args.file == "payload.bin"
    assert args.recipient == recipient_id


@pytest.mark.unit
def test_cli_output_result_json(capsys: pytest.CaptureFixture[str]) -> None:
    """output_result renders valid JSON when as_json is True."""
    data = {"status": "SUCCESS", "records": 42}
    output_result(data, as_json=True)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["status"] == "SUCCESS"
    assert parsed["records"] == 42


@pytest.mark.unit
def test_cli_main_version() -> None:
    """main(['version']) returns 0 and outputs version."""
    exit_code = main(["version"])
    assert exit_code == 0


@pytest.mark.unit
def test_cli_main_login_success() -> None:
    """main(['login']) dispatches to client and returns 0."""
    with patch("app.cli.main.F9l3Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.login.return_value = {"user": {"username": "alice", "role": "USER"}}
        mock_client_cls.return_value = mock_instance

        exit_code = main(["login", "-u", "alice", "-p", "pass123"])
        assert exit_code == 0
        mock_instance.login.assert_called_once_with(username="alice", password="pass123")


@pytest.mark.unit
def test_cli_main_send_success() -> None:
    """main(['send']) dispatches send_file and returns 0."""
    with patch("app.cli.main.F9l3Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.send_file.return_value = {"id": "test-uuid", "state": "ENCRYPTED"}
        mock_client_cls.return_value = mock_instance

        exit_code = main(["send", "-f", "dummy.txt", "-r", "recipient-uuid"])
        assert exit_code == 0
        mock_instance.send_file.assert_called_once_with(
            recipient_id="recipient-uuid", file_path="dummy.txt"
        )


@pytest.mark.unit
def test_cli_main_receive_success() -> None:
    """main(['receive']) dispatches receive_file and returns 0."""
    with patch("app.cli.main.F9l3Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.receive_file.return_value = Path("out.bin")
        mock_client_cls.return_value = mock_instance

        exit_code = main(["receive", "-t", "transfer-uuid", "-o", "out.bin"])
        assert exit_code == 0
        mock_instance.receive_file.assert_called_once_with(
            transfer_id="transfer-uuid", output_path="out.bin"
        )


@pytest.mark.unit
def test_cli_main_error_handling() -> None:
    """CLI catches F9l3CliError, outputs error to stderr and returns code 1."""
    with patch("app.cli.main.F9l3Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.login.side_effect = F9l3CliError("Invalid credentials")
        mock_client_cls.return_value = mock_instance

        exit_code = main(["login", "-u", "baduser", "-p", "wrong"])
        assert exit_code == 1
