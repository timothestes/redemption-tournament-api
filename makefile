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
