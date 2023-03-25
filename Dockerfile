FROM python:slim-bullseye

ARG user=python
ARG configPath=/config

VOLUME ["${configPath}"]

RUN useradd -ms /bin/bash $user
RUN apt-get -qq update && apt-get -qq install --no-install-recommends -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p $configPath \
    && chown -R $user:$user $configPath

# install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

USER $user
WORKDIR /home/$user
ENV PATH="/home/${user}/.local/bin:${PATH}"

RUN pip install -q --upgrade pip

COPY requirements.txt .
RUN pip install -q -r requirements.txt

ENV VOLUME_CONFIG_PATH="${configPath}/volumes.yaml"

COPY deploy-samba-server.py .
COPY default-helmrelease-template.yaml.j2 .
COPY entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]
