FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    openvswitch-switch \
    iproute2 \
    iputils-ping \
    net-tools \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

COPY start_ovs.sh /usr/local/bin/start_ovs.sh
RUN chmod +x /usr/local/bin/start_ovs.sh

WORKDIR /overlay

CMD ["bash"]
