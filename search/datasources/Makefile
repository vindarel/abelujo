pip:
	pip install -r requirements.txt

npm:
	npm install

install: pip npm

decitre:
	@cd frFR/decitre/ && python test_end2end.py

casadellibro:
	@cd esES/casadellibro/ && python test_end2end.py

testscrapers: decitre casadellibro
