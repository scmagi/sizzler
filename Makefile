upload-test: setup.py
	python3 setup.py sdist
	twine upload -r pypitest --skip-existing --config-file sizzler.pypirc dist/*

upload-release: setup.py
	python3 setup.py sdist
	twine upload -r pypi --skip-existing --config-file sizzler.pypirc dist/*
