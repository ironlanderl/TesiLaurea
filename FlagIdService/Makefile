.PHONY: run
run: .venv
	./.venv/bin/python app.y

.PHONY: run-new
run-new: .venv
	./.venv/bin/python app.y --reset

.PHONY: test
test: .venv
	./.venv/bin/pytest -v --durations=0 --showlocals

.venv: 
	uv venv .venv
	uv pip install -r requirements.txt
