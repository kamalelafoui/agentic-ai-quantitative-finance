.PHONY: install demo serve api test validate build clean

install:
	python -m pip install -r requirements-dev.txt

demo:
	python main.py demo

serve:
	python main.py serve

api:
	python main.py api

test:
	pytest -q

validate:
	python main.py validate --run

build:
	python main.py build

clean:
	rm -rf __pycache__ .pytest_cache
