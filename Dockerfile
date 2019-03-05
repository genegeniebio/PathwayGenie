FROM python:2.7

COPY . /
WORKDIR /

ARG VIENNA_VERSION="ViennaRNA-2.4.11"

RUN curl -fsSL https://www.tbi.univie.ac.at/RNA/download/sourcecode/2_4_x/$VIENNA_VERSION.tar.gz -o /opt/$VIENNA_VERSION.tar.gz \
	&& tar zxvf /opt/$VIENNA_VERSION.tar.gz -C /opt/ \
	&& cd /opt/$VIENNA_VERSION \
	&& ./configure \
	&& make \
	&& make install \
	&& cd / \
	&& pip install --upgrade pip \
	&& pip install -r requirements.txt --upgrade

CMD ["python", "-u", "app.py"]