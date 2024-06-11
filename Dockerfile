FROM python:3

# make and copy over and change directory
RUN mkdir app
COPY / /app
WORKDIR /app

# update and upgrade debian packages
RUN apt-get update && apt-get -y upgrade

# install all the python packages
RUN pip install -r requirements.txt

# expose the port and then run gunicorn
EXPOSE 5000
CMD gunicorn --bind 0.0.0.0:5000 'app:create_app("PROD")'