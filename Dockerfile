FROM python:2.7
ARG SERVICE_NAME
ARG SERVICE_VERSION
ENV SERVICE_NAME $SERVICE_NAME
ENV SERVICE_VERSION $SERVICE_VERSION
RUN mkdir /app
COPY . /app
RUN touch /app/.env
RUN pip install -r /app/requirements.txt
RUN pip install gunicorn
WORKDIR /app
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:80", "-b", "unix:coredb-service-aggregation.sock", "app:app"]