.PHONY: lint

lint:
	mypy rs274.py
	pydocstyle rs274.py
	flake8 --max-line-length=100 rs274.py
