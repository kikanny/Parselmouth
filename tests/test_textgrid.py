import pytest

import parselmouth

import sys

from builtins import str  # Python 2 compatibility


def test_create(text_grid_path):
	assert parselmouth.TextGrid(0.0, 1.0) == parselmouth.TextGrid(0.0, 1.0, [], [])
	assert parselmouth.TextGrid(0.0, 1.0, ["a", "b", "c", "d", "e"], ["b", "d", "e"]) == parselmouth.TextGrid(0.0, 1.0, "a b c d e", "b d e")
	assert parselmouth.TextGrid(0.0, 1.0, "a b c d e", "b d e") == parselmouth.praat.call("Create TextGrid", 0.0, 1.0, "a b c d e", "b d e")
	assert isinstance(parselmouth.read(text_grid_path), parselmouth.TextGrid)
	with pytest.raises(parselmouth.PraatError, match="The end time should be greater than the start time"):
		parselmouth.TextGrid(1.0, 0.0)
	with pytest.raises(parselmouth.PraatError, match="Point tier name 'c' is not in list of all tier names"):
		parselmouth.TextGrid(0.0, 1.0, ["a", "b"], ["a", "c", "d"])


def test_tgt(text_grid_path):
	tgt = pytest.importorskip('tgt')

	text_grid = parselmouth.read(text_grid_path)  # TODO Replace with TextGrid constructor taking filename?
	assert str('\n').join(map(str, text_grid.to_tgt().tiers)) == str('\n').join(map(str, tgt.read_textgrid(text_grid_path, 'utf-8', include_empty_intervals=True).tiers))
	assert parselmouth.TextGrid.from_tgt(text_grid.to_tgt()) == text_grid


def test_tgt_missing(text_grid_path, monkeypatch):
	monkeypatch.setitem(sys.modules, 'tgt', None)

	with pytest.raises(RuntimeError, match="Could not import 'tgt'"):
		parselmouth.read(text_grid_path).to_tgt()
	with pytest.raises(TypeError, match="incompatible function arguments"):
		parselmouth.TextGrid.from_tgt(None)


def test_tgt_exceptions(text_grid_path, monkeypatch):
	tgt = pytest.importorskip('tgt')

	class MockTextGrid:
		def __init__(self, *args, **kwargs):
			pass
	monkeypatch.setattr(tgt, "TextGrid", MockTextGrid)

	with pytest.raises(AttributeError, match=r"'MockTextGrid' object has no attribute '.*'|MockTextGrid instance has no attribute '.*'"):  # Python 2 compatibility
		parselmouth.read(text_grid_path).to_tgt()
	with pytest.raises(AttributeError, match=r"'MockTextGrid' object has no attribute '.*'|MockTextGrid instance has no attribute '.*'"):  # Python 2 compatibility
		parselmouth.TextGrid.from_tgt(MockTextGrid())
