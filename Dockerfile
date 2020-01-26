FROM python:3.8

WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "app.py"]

EXPOSE 80
COPY . /app
