pip install pandas
pip install synbiochem-py

set PYTHONPATH=%PYTHONPATH%;.

python \
	scripts/plasmid_writer.py \
	scripts/in.csv \
	scripts/out.csv \
	https://ice.synbiochem.co.uk \
	USERNAME \
	PASSWORD \
	synbiochem \