FROM gcr.io/google-appengine/python

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
# Use -p python3 or -p python3.7 to select python version. Default is version 2.
RUN virtualenv /env -p python3.7

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

# Issues experienced with ViennaRNA-2.4.14, therefore retaining 'stable' version:
ARG VIENNA_VERSION="ViennaRNA-2.4.11"

RUN curl -fsSL https://www.tbi.univie.ac.at/RNA/download/sourcecode/2_4_x/$VIENNA_VERSION.tar.gz -o /opt/$VIENNA_VERSION.tar.gz \
	&& tar zxvf /opt/$VIENNA_VERSION.tar.gz -C /opt/ \
	&& cd /opt/$VIENNA_VERSION \
	&& ./configure --without-perl \
	&& make \
	&& make install
	
ENV PYTHONPATH /usr/local/lib/python3.7/site-packages:$PYTHONPATH

# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Add the application source code.
ADD . /app

# Run a WSGI server to serve the application. gunicorn must be declared as
# a dependency in requirements.txt.
CMD gunicorn -t 3600 -b :$PORT main:app