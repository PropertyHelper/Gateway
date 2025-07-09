FROM python:3.10
RUN pip install poetry
WORKDIR /opt/app

COPY main.py poetry.lock pyproject.toml /opt/app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

COPY ./src /opt/app/src
CMD ["python", "main.py"]
