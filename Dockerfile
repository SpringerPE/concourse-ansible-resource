# Pull base image
FROM alpine:3.6
LABEL Description="Concourse Ansible resource" Vendor="SpringerNature Platform Engineering" Version="1.0"
MAINTAINER SpringerNature Platform Engineering platform-engineering@springernature.com

# Base packages
# Build dependencies
RUN ln -s /lib /lib64 \
    && \
        apk --upgrade add --no-cache \
            bash \
            sudo \
            curl \
            zip \
            jq \
            xmlsec \
            yaml \
            libc6-compat \
            python3 \
            libxml2 \
            py-lxml \
            py-pip \
            openssl \
            ca-certificates \
            openssh-client \
            rsync \
            git \
    && \
        apk --upgrade add --no-cache --virtual \
            build-dependencies \
            build-base \
            python3-dev \
            libffi-dev \
            openssl-dev \
            linux-headers \
            libxml2-dev

# Ansible installation
ADD requirements.txt /opt/
RUN pip3 install --upgrade --no-cache-dir -r /opt/requirements.txt

RUN apk del \
        build-dependencies \
        build-base \
        python3-dev \
        libffi-dev \
        openssl-dev \
        linux-headers \
        libxml2-dev \
    && \
        rm -rf /var/cache/apk/*

RUN mkdir -p ~/.ssh
RUN echo $'Host *\nStrictHostKeyChecking no' > ~/.ssh/config
RUN chmod 400 ~/.ssh/config

# Default config
COPY ansible/ /etc/ansible/

# Install tests
COPY tests/ /opt/resource/tests/

# install resource assets
COPY assets/ /opt/resource/

# install tests
#ADD scripts/* /tmp/
#RUN /tmp/install_test.sh


# test
#RUN /tmp/test.sh
#RUN /tmp/cleanup_test.sh

# default command: display local setup
CMD ["ansible", "-c", "local", "-m", "setup", "all"]
# CMD [ "ansible-playbook", "--version" ]
