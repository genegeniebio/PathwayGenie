FROM python:2.7-alpine

COPY . /
WORKDIR /

RUN apk add --no-cache --virtual build-dependencies gcc musl-dev make python-dev cmake g++ gfortran \
  && ln -s /usr/include/locale.h /usr/include/xlocale.h \
  && cd /nupack3.0.6 \
  && make clean \
  && make \
  && cd / \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apk del build-dependencies \
  && apk add --no-cache libstdc++ \
  && rm -rf /var/cache/apk/*

ENV PATH /nupack3.0.6/bin:${PATH}
ENV NUPACKHOME /nupack3.0.6/

ENTRYPOINT ["python"]
CMD ["app.py"]