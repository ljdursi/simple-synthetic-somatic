#!/bin/bash

readonly URL=ftp://ftp.sanger.ac.uk/pub/project/PanCancer/
readonly dir=reference

mkdir -p "${dir}"
cd "${dir}"

function compress_and_index {
    local file=$1
    bgzip -i "$file"
    samtools faidx "${file}.gz"
    bwa index "${file}.gz"
    zcat "${file}.gz" > "${file}"
}

wget "${URL}/genome.fa.gz"
gunzip genome.fa

sed -ne '/^>20 dna:.*/,/^>21 dna:.*/p' genome.fa \
    | head -n -1 \
    > chr20.fa

compress_and_index chr20.fa
compress_and_index genome.fa
