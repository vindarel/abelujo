# Goal: install Abelujo as on a fresh Debian,
# check doesn't fail and access to the app.
FROM debian:8.0
MAINTAINER vindarel <ehvince@mailz.org>
EXPOSE 8000
RUN apt-get update
RUN apt-get install -y git-core \
    make \
    sudo
WORKDIR /root/
RUN git clone https://gitlab.com/vindarel/abelujo.git
WORKDIR /root/abelujo
RUN git pull
RUN make debian
RUN ["/bin/bash", "-c", "source venv_create.sh", "&& make install"]
CMD ["/bin/bash", "-c", "source venv_create.sh", "python manage.py runserver 0.0.0.0:8000"]
# now we access the app.
