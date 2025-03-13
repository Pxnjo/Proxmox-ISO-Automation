FROM python:3.11.9
WORKDIR /usr/local/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main_project ./main_project
EXPOSE 443

VOLUME ["/usr/local/app/main_project/logs"]

ENTRYPOINT [ "python3", "main_project/script.py" ]