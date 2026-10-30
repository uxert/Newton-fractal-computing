FROM python:3.13.17

WORKDIR /app

COPY . .
RUN pip install -r requirements/http-server.txt

CMD ["python", "-m", "newton_raphson.server.main_server"]