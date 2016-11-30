FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /
WORKDIR /
RUN cd /nupack3.0.6 && make clean && make
ENV PATH /nupack3.0.6/bin:${PATH}
ENV NUPACKHOME /nupack3.0.6/
RUN pip install --upgrade pip
RUN pip install numpy
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py", "80"]