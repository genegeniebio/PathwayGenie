c:\Python27\Scripts\pip install pandas
c:\Python27\Scripts\pip install synbiochem-py

set PYTHONPATH=%PYTHONPATH%;.

python scripts/plasmid_writer.py scripts/plasmid_writer_in.csv scripts/plasmid_writer_out.csv https://ice.synbiochem.co.uk USERNAME PASSWORD synbiochem

pause