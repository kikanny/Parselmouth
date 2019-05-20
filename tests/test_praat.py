import pytest

import parselmouth

import itertools
import numpy as np
import os
import textwrap


def test_call_return_many(sound):
	stereo_sound = sound.convert_to_stereo()
	channels = parselmouth.praat.call(stereo_sound, "Extract all channels")
	assert len(channels) == 2
	assert np.all(channels[0].values == sound.values)
	assert np.all(channels[1].values == sound.values)


def test_call_with_extra_objects(sound):
	new = parselmouth.Sound(np.zeros((sound.n_channels, sound.n_samples)), sampling_frequency=sound.sampling_frequency, start_time=sound.start_time)
	sound.name = "the sound"
	parselmouth.praat.call(new, "Formula", "self [col] + Sound_the_sound [col]", extra_objects=[sound])
	assert sound == new

	with pytest.raises(parselmouth.PraatError, match=r"No such object \(note: variables start with lower case\)"):
		parselmouth.praat.call(new, "Formula", "self [col] + Sound_the_sound [col]")


def test_call_parameters(sound):
	assert parselmouth.praat.call(sound, "Add", 0.1) is None
	assert parselmouth.praat.call(sound, "Add", -1) is None
	assert parselmouth.praat.call(sound, "Override sampling frequency", 44100) is None
	with pytest.raises(parselmouth.PraatError, match=r"Argument \".*\" must be greater than 0"):
		assert parselmouth.praat.call(sound, "Override sampling frequency", -10.0) is None

	assert parselmouth.praat.call(sound, "Get time from sample number", 1) == sound.get_time_from_index(1)
	assert tuple(map(int, parselmouth.PRAAT_VERSION.split("."))) < (6, 0, 47)  # Replace with commented assert underneath once Praat version gets updated
	# with pytest.raises(parselmouth.PraatError, match=r"Argument \".*\" should be a whole number"):
	# 	assert parselmouth.praat.call(sound, "Get time from sample number", 0.5) != sound.get_time_from_index(1)
	assert parselmouth.praat.call(sound, "Set value at sample number", 1, 0.0) is None
	with pytest.raises(parselmouth.PraatError, match=r"Argument \".*\" should be a positive whole number"):
		assert parselmouth.praat.call(sound, "Set value at sample number", 0, -1, 0.0) is None

	assert parselmouth.praat.call(sound, "To Spectrum", True) == parselmouth.praat.call(sound, "To Spectrum", 1)
	assert parselmouth.praat.call(sound, "To Spectrum", False) == parselmouth.praat.call(sound, "To Spectrum", "no")

	assert parselmouth.praat.call(sound, "To TextGrid", "points intervals", "points").class_name == "TextGrid"
	assert parselmouth.praat.call("Create Sound from formula", "someSound", 1, 0, 1, 44100, "1/2").name == "someSound"

	many_channels = parselmouth.Sound(np.zeros((10, 1600)), 16000)
	assert parselmouth.praat.call(many_channels, "Extract channels", np.array([2, 3, 5, 7])).n_channels == 4
	assert parselmouth.praat.call(many_channels, "Extract channels", [2, 3, 5, 7]).n_channels == 4
	with pytest.raises(parselmouth.PraatError, match=r"Argument \".*\" should be a numeric vector, not a number"):
		assert parselmouth.praat.call(many_channels, "Extract channels", 4) == 1
	with pytest.raises(parselmouth.PraatError, match=r"Argument \".*\" should be a numeric vector, not a numeric matrix"):
		assert parselmouth.praat.call(many_channels, "Extract channels", np.array([[2, 3, 5, 7]])) == 4

	# If a Praat command with a NUMMAT argument gets added, a test should be added


def test_run(sound_path):
	script = textwrap.dedent("""\
	Read from file: "{}"
	To Intensity: 100.0, 0.0, "yes"
	selectObject: 1
	selectObject: "Intensity the_north_wind_and_the_sun"
	""".format(sound_path))

	assert parselmouth.praat.run(script)[0] == parselmouth.Sound(sound_path).to_intensity()

	with pytest.raises(parselmouth.PraatError, match="Found 3 arguments but expected only 0."):
		parselmouth.praat.run(script, 42, "some_argument", True)


def test_run_with_parameters(sound_path):
	script = textwrap.dedent("""
	form Test
		positive minPitch 100.0
		real timeStep 0.0
		boolean subtractMean "yes"
	endform
	
	Read from file: "{}"
	To Intensity: minPitch, timeStep, subtractMean
	selectObject: 1
	selectObject: "Intensity the_north_wind_and_the_sun"
	""".format(sound_path))

	min_pitch = 75
	time_step = 0.05
	subtract_mean = False

	assert parselmouth.praat.run(script, min_pitch, time_step, subtract_mean)[0] == parselmouth.Sound(sound_path).to_intensity(min_pitch, time_step, subtract_mean)

	with pytest.raises(parselmouth.PraatError, match="Found 0 arguments but expected more."):
		parselmouth.praat.run(script)


def test_run_with_extra_objects(sound):
	new = parselmouth.Sound(np.zeros((sound.n_channels, sound.n_samples)), sampling_frequency=sound.sampling_frequency, start_time=sound.start_time)
	sound.name = "the sound"
	parselmouth.praat.run(new, "Formula: ~ self [col] + Sound_the_sound [col]", extra_objects=[sound])
	assert sound == new

	with pytest.raises(parselmouth.PraatError, match=r"No such object \(note: variables start with lower case\)"):
		parselmouth.praat.run(new, "Formula: ~ self [col] + Sound_the_sound [col]")


def test_run_sys_stdout(capsys):
	parselmouth.praat.run("writeInfo: 42")
	assert capsys.readouterr().out == "42"
	parselmouth.praat.run("appendInfo: 42")
	assert capsys.readouterr().out == "42"
	parselmouth.praat.run("writeInfoLine: 42")
	assert capsys.readouterr().out == "42\n"
	parselmouth.praat.run("writeInfoLine: \"The answer\", \" - \", 42\nappendInfo: \"The question - ?\"")
	assert capsys.readouterr().out == "The answer - 42\nThe question - ?"
	parselmouth.praat.run("writeInfoLine: \"The answer\", \" - \", 42\nwriteInfoLine: \"The question - ?\"")
	assert capsys.readouterr().out == "The answer - 42\nThe question - ?\n"
	parselmouth.praat.run("writeInfo: tab$, newline$")
	assert capsys.readouterr().out == "\t\n"


def test_run_with_capture_output():
	assert parselmouth.praat.run("writeInfo: 42", capture_output=True) == ([], "42")
	assert parselmouth.praat.run("appendInfo: 42", capture_output=True) == ([], "42")
	assert parselmouth.praat.run("writeInfoLine: 42", capture_output=True) == ([], "42\n")
	assert parselmouth.praat.run("writeInfoLine: \"The answer\", \" - \", 42\nappendInfo: \"The question - ?\"", capture_output=True) == ([], "The answer - 42\nThe question - ?")
	assert parselmouth.praat.run("writeInfoLine: \"The answer\", \" - \", 42\nwriteInfoLine: \"The question - ?\"", capture_output=True) == ([], "The question - ?\n")
	assert parselmouth.praat.run("writeInfo: tab$, newline$", capture_output=True) == ([], "\t\n")


def test_run_with_return_variables():
	script = textwrap.dedent("""\
	a = 42
	b$ = "abc"
	c# = {1, 1, 2, 3, 5, 8, 13, 21, 34}
	d## = outer##({1, (1 + sqrt(5)) / 2}, c#)
	""")

	objects, variables = parselmouth.praat.run(script, return_variables=True)
	assert objects == []
	assert 'a' in variables and 'a$' not in variables and isinstance(variables['a'], float) and variables['a'] == 42
	assert 'b$' in variables and 'b' not in variables and variables['b$'] == "abc"
	assert 'c#' in variables and 'c' not in variables and isinstance(variables['c#'], np.ndarray) and variables['c#'].dtype == np.dtype(float) and variables['c#'].shape == (9,) and np.all(variables['c#'] == [1, 1, 2, 3, 5, 8, 13, 21, 34])
	assert 'd##' in variables and 'd#' not in variables and isinstance(variables['d##'], np.ndarray) and variables['d##'].dtype == np.dtype(float) and variables['d##'].shape == (2, 9) and np.all(variables['d##'] == np.outer([1, (1 + np.sqrt(5)) / 2], [1, 1, 2, 3, 5, 8, 13, 21, 34]))
	assert set(variables.keys()) == {'a', 'b$', 'c#', 'd##', 'newline$', 'tab$', 'shellDirectory$', 'defaultDirectory$', 'preferencesDirectory$', 'homeDirectory$', 'temporaryDirectory$', 'macintosh', 'windows', 'unix', 'left', 'right', 'mono', 'stereo', 'all', 'average', 'praatVersion$', 'praatVersion'}


def test_run_with_capture_output_and_return_variables():
	script = textwrap.dedent("""\
	a = 42
	b$ = "abc"
	writeInfoLine: a
	appendInfoLine: b$
	""")

	objects, output, variables = parselmouth.praat.run(script, capture_output=True, return_variables=True)
	assert objects == []
	assert output == "42\nabc\n"
	assert 'a' in variables and 'b$' in variables


def test_run_file_relative_paths(sound_path, resources):
	script_path = resources["script.praat"]
	assert os.getcwd() != os.path.abspath(os.path.dirname(script_path))
	assert parselmouth.praat.run_file(script_path, os.path.relpath(sound_path, os.path.dirname(script_path)))[0] == parselmouth.Sound(sound_path)


def test_remove_referenced_objects(sound):
	mean = sound.values.mean()
	assert parselmouth.praat.call(sound, "Remove") is None
	assert sound.values.mean() == mean

	many_sounds = [sound.copy() for _ in range(10)]
	assert parselmouth.praat.run(many_sounds[:5], "select all\nRemove", extra_objects=many_sounds[5:]) == []
	assert all(s.values.mean() == mean for s in many_sounds)


def test_call_no_objects(sound):
	assert parselmouth.praat.call(sound, "Get number of samples") == sound.n_samples
	with pytest.raises(parselmouth.PraatError, match="Command \"Get number of samples\" not available for given objects."):
		assert parselmouth.praat.call("Get number of samples")


def test_praat_callback_prefixes():
	separators = {'nullptr', '0'}
	values = {'REAL', 'INTEGER', 'BOOLEAN', 'COMPLEX', 'STRING', 'NUMVEC', 'NUMMAT'}
	objects = {'NEW', 'NEW1', 'NEW2', 'NEWMANY', 'NEWTIMES2', 'READ1', 'READMANY'}
	info = {'HINT', 'INFO', 'LIST'}
	nothing = {'HELP', 'MODIFY', 'PRAAT', 'PREFS', 'SAVE', 'GRAPHICS'}
	exception = {'PLAY', 'RECORD1', 'WINDOW', 'MOVIE'}
	weird = {'BUG', 'DANGEROUS'}

	prefixes = set(action[2].split('_')[0] for action in itertools.chain(parselmouth.praat._get_actions(), parselmouth.praat._get_menu_commands()))
	assert prefixes == separators | values | objects | info | nothing | exception | weird
