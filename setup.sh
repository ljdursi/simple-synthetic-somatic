#!/bin/bash

# download and index the references
./scripts/get-reference.sh

# download and index ART for simulating reads
readonly URL=http://www.niehs.nih.gov/research/resources/assets/docs
readonly ART_TGZ=artbinmountrainier20160605linux64tgz.tgz

wget ${URL}/${ART_TGZ}
tar -xzvf ${ART_TGZ}
rm ${ART_TGZ}
