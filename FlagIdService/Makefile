.PHONY: run
run: .venv
	./.venv/bin/python app.py

.PHONY: run-new
run-new: .venv
	./.venv/bin/python app.py --reset

.PHONY: test
test: .venv
	./.venv/bin/pytest -v --durations=0 --showlocals

.venv: 
	uv venv .venv
	uv pip install -r requirements.txt
