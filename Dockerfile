FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY database.py config.py /app/

EXPOSE 45556

CMD ["python", "backend/main.py"]
