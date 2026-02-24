FROM python:3.13

COPY options/ /src

WORKDIR /src

RUN apt-get update -y && apt-get install -y pip

RUN pip3 install -r requirements.txt

CMD ["python3", "index.py"]