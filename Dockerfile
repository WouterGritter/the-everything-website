FROM python:3.11

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY *.py ./

CMD ["python", "-u", "main.py"]
