## Simple synthetic somatic data for PCAWG validation/merge pipeline

A very simple generator for simple somatic read and caller data for
demonstration and testing the PCAWG-1 somatic call validation and merge
pipeline.  

Uses [ART](http://www.niehs.nih.gov/research/resources/software/biostatistics/art/) to generate 
synthetic reads for a normal bam (currently hg19 with no germline mutations) 
and [BAMSurgeon](https://github.com/adamewing/bamsurgeon) to add somatic SNVs and indels.

Requirements:
* BAMSurgeon, which requires:
  - velvet
  - bwa
  - samtools, htslib
  - bcftools
  - picard
  - exonerate
* ART (downloaded by the setup.sh script)

## Running

Running the following

```
./setup.sh         # downloads/indexes reference: takes some time!
./build_small_data small
```

will result in a directory `small` containing simulated normal and tumour BAMs for chr20, VCFs for five callers 
that include false positives and negatives, and truth datasets.  Similarly,

```
./build_full_data full
```

(which will take much longer) will generate synthetic data for the whole genome.


## Running with Docker

The provided Dockerfile allows running these tools as a container:

```
docker build -t simple_synthetic_somatic .
docker run -it -v ${PWD}:/output simple_synthetic_somatic generate small   # generates data for chr20
docker run -it -v ${PWD}:/output simple_synthetic_somatic generate full    # generates whole-genome data
```
