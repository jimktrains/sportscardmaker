venv:
	python -m venv venv

install-pip:
	bash -c "source venv/bin/activate; pip install -r requirements.txt"
