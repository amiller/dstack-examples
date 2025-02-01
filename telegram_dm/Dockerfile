FROM python:3-slim

WORKDIR /workdir
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN playwright install

COPY telegram_login.py ./
COPY telegram_run.py ./

ENTRYPOINT [ ]
CMD [ "python3", "telegram_run.py" ]
