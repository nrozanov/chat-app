FROM --platform=linux/amd64 python:3.10.6 as builder
ARG poetry_extra_flags=

RUN pip install --upgrade pip && pip install poetry==1.4.1

COPY ./pyproject.toml ./poetry.lock /

RUN poetry export --without-hashes ${poetry_extra_flags} -f requirements.txt -o requirements.txt
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt

FROM --platform=linux/amd64 python:3.10.6-slim
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app
COPY . .

RUN chmod +x docker-entrypoint.sh

CMD ["/usr/src/app/docker-entrypoint.sh"]
