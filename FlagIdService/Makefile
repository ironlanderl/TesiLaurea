.PHONY: run
run: .venv
	./.venv/bin/flask run

.PHONY: test
test: .venv
	./.venv/bin/pytest -v --durations=0 --showlocals

.venv: 
	uv venv .venv
	uv pip install -r requirements.txt
