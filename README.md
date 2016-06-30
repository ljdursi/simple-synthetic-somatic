# Simple synthetic somatic data for PCAWG validation/merge pipeline

A very simple generator for simple somatic read and caller data for
demonstration and testing the PCAWG-1 somatic call validation and merge
pipeline.  

Uses [ART](http://www.niehs.nih.gov/research/resources/software/biostatistics/art/) to generate 
synthetic reads for a normal bam (currently hg19 with no germline mutations) 
and [BAMSurgeon](https://github.com/adamewing/bamsurgeon) to add somatic SNVs and indels.
