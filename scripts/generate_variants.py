#!/usr/bin/env python
from __future__ import print_function
import sys
import argparse
import numpy
import numpy.random
import random

def readfasta(infile):
    labels = []
    sequences = []

    curlabel = None
    cursequence = ""

    def updatelists():
        if len(cursequence) is not 0:
            sequences.append(cursequence)
            if curlabel is not None:
                labels.append(curlabel.split()[0])
            else:
                labels.append('seq'+str(len(sequences)))

    for line in infile:
        if line[0] == ">":
            updatelists()
            cursequence = ""
            curlabel = line[1:].strip()
        else:
            cursequence += line.strip()

    updatelists()
    return list(zip(labels, sequences))

class Caller(object):
    """
    Simulates a caller which 'selects' calls to make based on a randomly-
    generated precision and recall
    """
    def __init__(self, name, snvs_valid, snvs_invalid, indels_valid, indels_invalid, sensitivity=None, precision=None):
        self.name = name
        self.sensitivity = random.uniform(0.5, 0.95) if not sensitivity else sensitivity
        self.precision = random.uniform(0.5, 0.95) if not precision else precision

        goodfrac = self.sensitivity
        badfrac = self.sensitivity*(1.-self.precision)/self.precision

        self.snvs = random.sample(snvs_valid, int(goodfrac*len(snvs_valid)))
        self.indels = random.sample(indels_valid, int(goodfrac*len(indels_valid)))

        self.snvs += random.sample(snvs_invalid, min(int(badfrac*len(snvs_valid)), len(snvs_invalid)))
        self.indels += random.sample(indels_invalid, min(int(badfrac*len(indels_valid)), len(indels_invalid)))

        self.snvs = sorted(self.snvs)
        self.indels = sorted(self.indels)

    def toVCF(self, filename, directory, snvs=False, indels=False):
        "Output to a VCF file with given filename; optionally output variant types"
        variants = []
        if snvs:
            variants += self.snvs
        if indels:
            variants += self.indels
        variants = sorted(variants)

        with open(directory+"/"+filename, 'w') as out:
            print('##fileformat=VCFv4.1', file=out)
            print('##caller_name='+str(self.name), file=out)
            print('##sensitivity='+str(int(self.sensitivity*100)*1./100.), file=out)
            print('##precision='+str(int(self.precision*100)*1./100.), file=out)
            print('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO', file=out)
            for chrom, pos, ref, alt in variants:
                print('{}\t{}\t.\t{}\t{}\t.\t.\t.'.format(chrom, pos, ref, alt), file=out)

    def toBamSurgeonBED(self, filename, directory, snvs=True, indels=True):
        # Not really BED - 1-indexed like VCF
        variants = []
        if snvs:
            variants += self.snvs
        if indels:
            variants += self.indels
        variants = sorted(variants)

        #Need VAFs for BED
        clone_vafs = [0.2, 0.33, 0.5]
        def get_vaf():
            base_vaf = random.choice(clone_vafs)
            ntrials = 30
            return int(numpy.random.binomial(ntrials, base_vaf)*1./ntrials*1000)/1000.

        with open(directory+"/"+filename, 'w') as out:
            for chrom, pos, ref, alt in variants:
                if len(ref) == len(alt):
                    print('{}\t{}\t{}\t{}\t{}'.format(chrom, pos, pos, get_vaf(), alt), file=out)
                else:
                    #indel
                    endpos = pos+len(ref)
                    varstr = alt[1:] if len(ref) < len(alt) else ref[1:]
                    vartype = "INS" if len(ref) < len(alt) else "DEL"
                    print('{}\t{}\t{}\t{}\t{}\t{}'.format(chrom, pos, endpos, get_vaf(), vartype, varstr), file=out)


def locations_from_starts(starts, cumulative_sizes):
    """
    Returns list of (chromosome number, offset)
    given starts and cumulative sizes.

    Requires that starts is sorted
    """
    cur_chromosome = 0
    last_size, cur_size = 0, cumulative_sizes[cur_chromosome]
    locations = []
    for start in starts:
        while start > cur_size:
            cur_chromosome += 1
            last_size, cur_size = cur_size, cumulative_sizes[cur_chromosome]
        locations.append((cur_chromosome, start-last_size))
    return locations

def snvs_from_starts(genome, snv_starts, cumulative_sizes):
    """
    Returns list of (chrom, pos, ref, alt) SNVs given the starting positions
    Positions corresponding to 'N' refs are dropped
    """
    locations = locations_from_starts(snv_starts, cumulative_sizes)
    bases = ['A', 'C', 'G', 'T']
    base_set = set(bases)
    other_bases = {base:[b for b in bases if not b == base] for base in bases}

    snvs = []
    for chromnum, posnum in locations:
        chr_name = genome[chromnum][0]
        ref = genome[chromnum][1][posnum]
        if not ref in base_set:
            continue
        alt = random.choice(other_bases[ref])
        snvs.append((chr_name, posnum+1, ref, alt))
    return snvs

def random_string(bases, length):
    return "".join([random.choice(bases) for _ in range(length)])

def indels_from_starts(genome, indel_starts, cumulative_sizes, max_size=100):
    """
    Returns list of (chrom, pos, ref, alt) SNVs given the starting positions
    Positions corresponding to 'N' refs are dropped
    """
    locations = locations_from_starts(indel_starts, cumulative_sizes)
    bases = ['A', 'C', 'G', 'T']
    base_set = set(bases)

    indels = []
    for chromnum, posnum in locations:
        chr_name = genome[chromnum][0]
        indelsize = min(int(numpy.random.pareto(2.) + 1), max_size)
        if random.choice([True, False]):
            ref = genome[chromnum][1][posnum]
            alt = ref+random_string(bases, indelsize)
        else:
            ref = genome[chromnum][1][posnum:posnum+indelsize+1]
            alt = genome[chromnum][1][posnum]
        if len(ref) == len(alt):
            continue
        validbases = [base in base_set for base in ref]
        if not all(validbases):
            continue
        indels.append((chr_name, posnum+1, ref, alt))
    return indels

def variants_from_genome(fasta, n_snvs, n_indels, max_indel_size):
    """
    Reads a genome file (.fasta), selects n valid snvs and indels
    given the parameters.
    """
    valid_chromosomes = [str(i) for i in range(1, 22)] + ["X", "Y"]
    genome = readfasta(fasta)
    genome = [(chrom, seq) for chrom, seq in genome \
                            if chrom in valid_chromosomes]

    sizes = numpy.array([len(seq) for chrom, seq in genome])
    cum_sizes = numpy.cumsum(sizes)

    snv_starts = sorted(random.sample(range(cum_sizes[-1]), n_snvs))
    indel_starts = sorted(random.sample(range(cum_sizes[-1]), n_indels))

    return snvs_from_starts(genome, snv_starts, cum_sizes), \
            indels_from_starts(genome, indel_starts, cum_sizes, max_indel_size)

def select_valid(variants, nvalid):
    """
    Takes a sorted list, shuffles it, selects nvalid "good" ones and the rest "bad",
    and re-sorts
    """
    random.shuffle(variants)
    return sorted(variants[:nvalid]), sorted(variants[nvalid:])

def main():
    """
    Driver function - takes arguments from command line and generates variants.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('genome', type=argparse.FileType('r'))
    parser.add_argument('-s', '--num_snvs', type=int, default=3000, help='Number of synthetic somatic SNVs')
    parser.add_argument('-i', '--num_indels', type=int, default=300, help='Number of synthetic somatic Indels')
    parser.add_argument('-m', '--max_indel_size', type=int, default=100, help='Maximum indel size')
    parser.add_argument('-c', '--num_callers', type=int, default=5, help='Number of callers')
    parser.add_argument('-d', '--out_dir', type=str, default='.', help='Output Directory')

    args = parser.parse_args()

    snv, indel = variants_from_genome(args.genome, 5*args.num_snvs,
                                      5*args.num_indels, args.max_indel_size)

    valid_snvs, invalid_snvs = select_valid(snv, args.num_snvs)
    valid_indels, invalid_indels = select_valid(indel, args.num_indels)

    truth = Caller("truth", valid_snvs, [], valid_indels, [], sensitivity=1., precision=1.)
    truth.toVCF("truth.vcf", args.out_dir, snvs=True, indels=True)

    truth.toBamSurgeonBED("truth.snv.bed", args.out_dir, snvs=True, indels=False)
    truth.toBamSurgeonBED("truth.indel.bed", args.out_dir, snvs=False, indels=True)
    for i in range(args.num_callers):
        callername = "caller"+str(i)
        caller = Caller(callername, valid_snvs, invalid_snvs, valid_indels, invalid_indels)
        caller.toVCF(callername+".snv.vcf", args.out_dir, snvs=True)
        caller.toVCF(callername+".indel.vcf", args.out_dir, indels=True)

    return 0

if __name__ == "__main__":
    sys.exit(main())
