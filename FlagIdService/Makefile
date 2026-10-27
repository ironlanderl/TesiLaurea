.PHONY: run
run: .venv
	./.venv/bin/flask run


.venv: 
	uv venv .venv
	uv pip install -r requirements.txt
