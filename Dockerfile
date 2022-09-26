FROM python:3.10

WORKDIR "/home/dev/app"
RUN useradd -d "/home/dev" dev \
	&& chown dev:dev "/home/dev"
USER dev

ENV PATH="$PATH:/home/dev/app/.local/bin"
COPY requirements.* ./
RUN for item in $( find ./requirements.* ); do echo $item && python -m pip install -r $item; done
ENTRYPOINT [ "bash" ]

