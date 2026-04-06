"""Tests for the Hairpin CLI entrypoint."""

from hairpin import __main__ as cli


class TestMain:
    def test_runs_file_with_program_args(self, tmp_path, capsys):
        program_path = tmp_path / "program.hp"
        program_path.write_text("program-args print", encoding="utf-8")

        result = cli.main([str(program_path), "alpha", "beta"])

        assert result == 0
        assert capsys.readouterr().out == "(alpha beta)"

    def test_reports_hairpin_errors(self, tmp_path, capsys):
        program_path = tmp_path / "program.hp"
        missing_path = tmp_path / "missing.txt"
        program_path.write_text("program-args head read-file", encoding="utf-8")

        result = cli.main([str(program_path), str(missing_path)])

        captured = capsys.readouterr()
        assert result == 1
        assert captured.out == ""
        assert f"Error: Cannot read file '{missing_path}'" in captured.err

    def test_starts_repl_without_program_file(self, monkeypatch):
        calls = []

        monkeypatch.setattr(cli, "repl", lambda: calls.append("repl"))

        result = cli.main([])

        assert result == 0
        assert calls == ["repl"]
