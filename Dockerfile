FROM snakepacker/python:all AS builder

RUN python3.13 -m venv /usr/share/python3/app
RUN /usr/share/python3/app/bin/pip install -U setuptools wheel

# bump this number for invalidating installing dependencies
# cache for following layers
ENV DOCKERFILE_VERSION=1

COPY dist/ /mnt/dist
RUN /usr/share/python3/app/bin/pip install -U /mnt/dist/*.whl

RUN find-libdeps /usr/share/python3/app > /usr/share/python3/app/pkgdeps.txt

########################################################################
FROM snakepacker/python:3.13 AS release

ADD packages.txt /usr/share/packages.txt
RUN xargs -ra /usr/share/packages.txt apt-install
ARG OHMYZSH_COMMIT=41c5b9677afaf239268197546cfc8e003a073c97
ARG OHMYZSH_SHA256=ce0b7c94aa04d8c7a8137e45fe5c4744e3947871f785fd58117c480c1bf49352
RUN curl -fsSL "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/${OHMYZSH_COMMIT}/tools/install.sh" -o /tmp/install.sh \
    && echo "${OHMYZSH_SHA256}  /tmp/install.sh" | sha256sum -c - \
    && sh /tmp/install.sh \
    && rm /tmp/install.sh

COPY --from=builder /usr/share/python3/app /usr/share/python3/app
RUN xargs -ra /usr/share/python3/app/pkgdeps.txt apt-install
RUN find /usr/share/python3/app/bin/ -name 'tty_aiohttp*' -exec ln -snf '{}' /usr/bin/ ';'
ENV APP_API_ADDRESS=0.0.0.0
ENV LANG=C.UTF-8
ENV TERM=xterm-256color


CMD ["tty_aiohttp"]
