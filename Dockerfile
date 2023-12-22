FROM python:3.9

WORKDIR /code
 
COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN pip install pytest

COPY ./app /code/app

COPY ./tests /code/tests

ENV AWS_DEFAULT_REGION=us-east-2

EXPOSE 8012

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8012"]