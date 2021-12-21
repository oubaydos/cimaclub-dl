FROM python:latest
WORKDIR /app
ADD . /app/
RUN pip install requests beautifulsoup4
CMD python index.py
