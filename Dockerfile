FROM python:2.7-alpine

COPY . /
WORKDIR /

RUN apk add --no-cache --virtual build-dependencies gcc musl-dev make \
  && cd /nupack3.0.6 \
  && make clean \
  && make \
  && cd / \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apk del build-dependencies

ENV PATH /nupack3.0.6/bin:${PATH}
ENV NUPACKHOME /nupack3.0.6/

ENTRYPOINT ["python"]
CMD ["app.py"]