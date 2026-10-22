"""Unit tests for noise detection and priority ranking."""

from src.mcp_git_sentinel.core.noise_filter import NoiseFilter


def test_lockfile_detection():
    assert NoiseFilter.is_noisy("package-lock.json") is True
    assert NoiseFilter.is_noisy("frontend/pnpm-lock.yaml") is True
    assert NoiseFilter.is_noisy("backend/poetry.lock") is True
    assert NoiseFilter.is_noisy("Cargo.lock") is True
    assert NoiseFilter.is_noisy("src/main.py") is False


def test_noisy_directories():
    assert NoiseFilter.is_noisy("node_modules/express/index.js") is True
    assert NoiseFilter.is_noisy("dist/bundle.js") is True
    assert NoiseFilter.is_noisy("build/output.bin") is True
    assert NoiseFilter.is_noisy("src/components/Button.tsx") is False


def test_noisy_extensions():
    assert NoiseFilter.is_noisy("assets/logo.png") is True
    assert NoiseFilter.is_noisy("dist/app.min.js") is True
    assert NoiseFilter.is_noisy("styles/main.min.css") is True
    assert NoiseFilter.is_noisy("scripts/app.js.map") is True
    assert NoiseFilter.is_noisy("docs/architecture.md") is False


def test_priority_ranking():
    core_score = NoiseFilter.get_file_priority("src/core/engine.py")
    test_score = NoiseFilter.get_file_priority("tests/test_engine.py")
    doc_score = NoiseFilter.get_file_priority("README.md")
    conf_score = NoiseFilter.get_file_priority("config.yaml")

    assert core_score > test_score
    assert test_score > doc_score
    assert doc_score > conf_score
