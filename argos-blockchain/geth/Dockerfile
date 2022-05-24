# Build Geth in a stock Go builder container
FROM ethereum/client-go:v1.10.2

MAINTAINER Volker Strobel <volker.strobel87@gmail.com>			

RUN apk add --no-cache ca-certificates

EXPOSE 4000 9800-9899 8545 8546 8547 30303 30303/udp

USER root
WORKDIR /root/

RUN apk add --no-cache --update git bash nodejs npm perl python3 python3-dev py3-pip build-base 
#RUN npm config set unsafe-perm true && npm install -g npm@next && npm config set unsafe-perm false
RUN cd /root &&\
    npm install solc@0.8.5 &&\
    npm install web3@1.3.4
RUN pip3 install --upgrade pip
RUN pip3 install web3 rpyc

COPY ./scripts /root/
COPY ./files/password /root/files/password
COPY ./templates /root/
RUN chmod a+x /root/start.sh
RUN chmod a+x /root/start_bootstrap.sh
#ADD app.json /root/eth-net-intelligence-api/app.json

ENTRYPOINT /root/start.sh
