c:\Python27\Scripts\pip install pandas
c:\Python27\Scripts\pip install synbiochem-py

set PYTHONPATH=%PYTHONPATH%;.

python scripts/strain_writer.py scripts/strain_writer_in.csv scripts/strain_writer_out.csv https://ice.synbiochem.co.uk USERNAME PASSWORD synbiochem

pause