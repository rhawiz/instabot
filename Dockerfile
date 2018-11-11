FROM python:3.5
RUN mkdir /app
COPY . /app
RUN touch /app/.env
RUN pip install -r /app/requirements.txt
RUN pip install gunicorn
RUN python /app/install_ffmpeg.py
RUN export DATABASE_URL=sqlite:////app/instabot.db
RUN python /app/db_create.py
WORKDIR /app
EXPOSE 5000
CMD [
]