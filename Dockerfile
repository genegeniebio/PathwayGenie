FROM python:2.7

COPY . /
WORKDIR /

RUN cd /nupack3.0.6 \
	&& make clean \
	&& make \
	&& cd / \
	&& pip install --upgrade pip \
	&& pip install -r requirements.txt

ENV PATH /nupack3.0.6/bin:${PATH}
ENV NUPACKHOME /nupack3.0.6/

ENTRYPOINT ["python"]
CMD ["app.py"]