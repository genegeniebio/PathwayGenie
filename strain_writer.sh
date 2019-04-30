pip install pandas
pip install synbiochem-py

export PYTHONPATH=$PYTHONPATH:.

python \
	scripts/strain_writer.py \
	scripts/strain_writer_in.csv \
	scripts/strain_writer_out.csv \
	https://ice.synbiochem.co.uk \
	USERNAME \
	PASSWORD \
	synbiochem \