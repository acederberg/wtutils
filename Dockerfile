FROM python:3.10

WORKDIR "/home/dev/app"
RUN useradd -d "/home/dev" dev \
	&& chown dev:dev "/home/dev"
USER dev

RUN find "./requirements*" | xargs -i python -m pip install -r {}
ENTRYPOINT [ "bash" ]

