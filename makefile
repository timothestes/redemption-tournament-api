.PHONY: shell exit install

# Command to activate the pipenv shell
shell:
	pipenv shell

# Command to deactivate the virtual environment
exit:
	exit

# Command to install all dependencies from the Pipfile
install:
	pipenv install

test:
	pytest --maxfail=1 --disable-warnings -q

run:
	python3 -m app
dev:
	python3 -m app
pdf:
	python3 -m src.utilities.text_to_pdf
webp:
	python3 -m scripts.generate_webp
data:
	python3 -m scripts.generate_json