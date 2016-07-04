FROM ubuntu:14.04
MAINTAINER Jonathan Dursi <jonathan@dursi.ca>

WORKDIR /root

RUN apt-get update && apt-get install -y software-properties-common

RUN add-apt-repository -y ppa:scipy/ppa

RUN apt-get install -y \
    pkg-config \
    python \
    python-numpy \
    python-scipy \
    python-pip \
    zlib1g-dev \
    git \
    wget \
    libtool \
    libncurses5-dev \
    libglib2.0-dev \
    unzip

RUN pip install cython
RUN pip install pysam

RUN mkdir $HOME/bin

RUN wget https://www.ebi.ac.uk/~zerbino/velvet/velvet_1.2.10.tgz
RUN tar xvzf velvet_1.2.10.tgz
RUN make -C velvet_1.2.10
RUN cp velvet_1.2.10/velvetg $HOME/bin
RUN cp velvet_1.2.10/velveth $HOME/bin

RUN git clone https://github.com/lh3/bwa.git
RUN make -C bwa
RUN cp bwa/bwa $HOME/bin

RUN wget https://github.com/samtools/htslib/releases/download/1.3.1/htslib-1.3.1.tar.bz2 && \
    tar -jxvf htslib-1.3.1.tar.bz2 && \
    cd htslib-1.3.1 && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd && \
    rm -f htslib-1.3.1.tar.bz2 && \
    rm -rf htslib-1.3.1

RUN wget https://github.com/samtools/samtools/releases/download/1.3.1/samtools-1.3.1.tar.bz2 && \
    tar -jxvf samtools-1.3.1.tar.bz2 && \
    cd samtools-1.3.1 && \
    ./configure --prefix=/usr --with-htslib=/usr && \
    make && \
    make install && \
    cd && \
    rm -f samtools-1.3.1.tar.bz2 && \
    rm -rf samtools-1.3.1

RUN wget https://github.com/samtools/bcftools/releases/download/1.3.1/bcftools-1.3.1.tar.bz2 && \
    tar -jxvf bcftools-1.3.1.tar.bz2 && \
    cd bcftools-1.3.1 && \
    make && \
    cp bcftools $HOME/bin && \
    cd && \
    rm -f bcftools-1.3.1.tar.bz2

RUN wget https://github.com/broadinstitute/picard/releases/download/1.131/picard-tools-1.131.zip
RUN unzip picard-tools-1.131.zip

RUN git clone https://github.com/adamewing/exonerate.git
RUN cd exonerate && ./configure --disable-dependency-tracking && make && make install

RUN git clone https://github.com/adamewing/bamsurgeon.git
RUN cd bamsurgeon && python setup.py install

RUN cp /root/bin/* /usr/bin

ADD . .
RUN ./setup.sh

VOLUME /root/reference
