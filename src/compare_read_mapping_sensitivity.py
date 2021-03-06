import glob
from multiprocessing import Process, Manager, Value, Semaphore
import os
import pysam
from random import random
import sys

from reference_vntr import load_unique_vntrs_data
from sam_utils import get_id_of_reads_mapped_to_vntr_in_samfile
from vntr_finder import VNTRFinder


def clean_up_tmp():
    os.system('rm -rf /tmp/*.sam')
    os.system('rm -rf /tmp/*.fasta')


def bowtie_alignment(fasta_file, output, param):
    os.system('bowtie2 -x hg19_chromosomes/hg19_bt2_idx --end-to-end -f %s -S %s --threads 24 --score-min L,-0.6,%s' % (fasta_file, output, param))


def bwa_alignment(fasta_file, output, param):
    os.system('bwa mem -T %s -t 24 hg19_chromosomes/CombinedHG19_Reference.fa %s > %s' % (param, fasta_file, output))


def save_reads_stat(file_name, reads):
    with open(file_name, 'w') as out:
        for read in reads:
            alignment_score = None
            for key, value in read.tags:
                if key == 'AS':
                    alignment_score = value
            out.write('%s %s\n' % (read.qname, alignment_score))


def get_positive_and_fn_reads_from_samfile(sam_file, reference_vntr, true_reads, read_length=150):
    alignment_file = pysam.AlignmentFile(sam_file, 'r', ignore_truncation=True)
    start = reference_vntr.start_point
    end = reference_vntr.start_point + reference_vntr.get_length()
    positive_reads = []
    false_negative_reads = []
    try:
        for read in alignment_file.fetch(until_eof=True):
            if read.is_unmapped:
                if read.qname in true_reads:
                    false_negative_reads.append(read)
                continue
            # if read.is_supplementary:
            #     continue
            # if read.is_secondary:
            #     continue
            if reference_vntr.chromosome == read.reference_name:
                if start - read_length < read.reference_start < end:
                    positive_reads.append(read)
                    continue
            if read.qname in true_reads:
                false_negative_reads.append(read)
    except IOError as err:
        print('Catched IOError: ', err)
        print('positive len:', len(positive_reads))
    return positive_reads, false_negative_reads


def write_hmm_scores(simulated_samfile, true_reads_hmm_scores, false_reads_hmm_scores, ref_vntr, true_reads):
    vntr_finder = VNTRFinder(ref_vntr)
    hmm = vntr_finder.get_vntr_matcher_hmm(150)

    manager = Manager()
    false_scores = manager.list()
    true_scores = manager.list()

    process_list = []
    sema = Semaphore(16)
    samfile = pysam.AlignmentFile(simulated_samfile, 'r', ignore_truncation=True)
    for read in samfile.fetch(until_eof=True):
        if read.seq.count('N') > 0:
            continue
        if True:
            if read.qname in true_reads:
                sema.acquire()
                p = Process(target=VNTRFinder.add_hmm_score_to_list, args=(sema, hmm, read, true_scores))
            else:
                if random() > 0.001:
                    continue
                sema.acquire()
                p = Process(target=VNTRFinder.add_hmm_score_to_list, args=(sema, hmm, read, false_scores))
            process_list.append(p)
            p.start()
        else:
            if vntr_finder.is_true_read(read):
                sema.acquire()
                p = Process(target=VNTRFinder.add_hmm_score_to_list, args=(sema, hmm, read, true_scores))
            else:
                if random() > 0.001:
                    continue
                sema.acquire()
                p = Process(target=VNTRFinder.add_hmm_score_to_list, args=(sema, hmm, read, false_scores))
            process_list.append(p)
            p.start()
    for p in process_list:
        p.join()

    with open(true_reads_hmm_scores, 'w') as out:
        for score in true_scores:
            out.write('%s\n' % score)
    with open(false_reads_hmm_scores, 'w') as out:
        for score in false_scores:
            out.write('%s\n' % score)


def find_info_by_mapping(sim_dir='simulation_data/', dir_index=0):
    reference_vntrs = load_unique_vntrs_data()
    id_to_gene = {119: 'DRD4', 1220: 'GP1BA', 1221: 'CSTB', 1214: 'MAOA', 1219: 'IL1RN'}
    gene_to_length = {'DRD4': 528, 'GP1BA': 39, 'CSTB': 168, 'MAOA': 30}
    clean_up_tmp()
    dirs = glob.glob(sim_dir+'/*')
    simulation_dir = dirs[dir_index]
    files = glob.glob(simulation_dir + '/*')
    for fasta_file in files:
        if fasta_file.endswith('WGS_30x.fasta'):
            gene_name = simulation_dir.split('/')[-1].split('_')[0]
            vntr_id = None
            for vid, gname in id_to_gene.items():
                if gname == gene_name:
                    vntr_id = vid
            ref_vntr = reference_vntrs[vntr_id]

            true_reads_file = fasta_file[:-6] + '_true_reads.txt'
            simulated_sam_file = fasta_file[:-6] + '.sam'
            if not os.path.exists(true_reads_file):
                region = [ref_vntr.start_point, ref_vntr.start_point + gene_to_length[gene_name]]
                true_reads = get_id_of_reads_mapped_to_vntr_in_samfile(simulated_sam_file, ref_vntr, region=region)
                with open(true_reads_file, 'w') as out:
                    for true_read in true_reads:
                        out.write('%s\n' % true_read)
            else:
                with open(true_reads_file) as input:
                    lines = input.readlines()
                    true_reads = [line.strip() for line in lines if line.strip() != '']

            true_reads_hmm_scores = fasta_file[:-6] + '_t_reads_hmm_score.txt'
            false_reads_hmm_scores = fasta_file[:-6] + '_f_reads_hmm_score.txt'
            if not os.path.exists(true_reads_hmm_scores):
                write_hmm_scores(simulated_sam_file, true_reads_hmm_scores, false_reads_hmm_scores, ref_vntr, true_reads)

            for i, parameter in enumerate([10]):
                positive_file = fasta_file[:-6] + '_bwa_%s_positive_supplementary_reads.txt' % abs(parameter)
                false_negative_file = fasta_file[:-6] + '_bwa_%s_fn_supplementary_reads.txt' % abs(parameter)
                if os.path.exists(positive_file) and os.path.exists(false_negative_file):
                    continue
                bwa_alignment_file = '/tmp/_gene%s_' % dir_index + 'bwa_alignment_%s.sam' % i
                bwa_alignment(fasta_file, bwa_alignment_file, parameter)
                positive_reads, fn_reads = get_positive_and_fn_reads_from_samfile(bwa_alignment_file, ref_vntr, true_reads)
                save_reads_stat(positive_file, positive_reads)
                save_reads_stat(false_negative_file, fn_reads)

                clean_up_tmp()

            for i, parameter in enumerate([-0.6, -2]):
                if i == 0:
                    continue
                positive_file = fasta_file[:-6] + '_bowtie_%s_positive_supplementary_reads.txt' % abs(parameter)
                false_negative_file = fasta_file[:-6] + '_bowtie_%s_fn_supplementary_reads.txt' % abs(parameter)
                if os.path.exists(positive_file) and os.path.exists(false_negative_file):
                    continue
                bowtie_alignment_file = '/tmp/_gene%s_' % dir_index + 'bowtie_alignment_%s.sam' % i
                bowtie_alignment(fasta_file, bowtie_alignment_file, parameter)
                positive_reads, fn_reads = get_positive_and_fn_reads_from_samfile(bowtie_alignment_file, ref_vntr, true_reads)
                save_reads_stat(positive_file, positive_reads)
                save_reads_stat(false_negative_file, fn_reads)
                if gene_name == 'MAOA':
                    os.system('cp %s /pedigree2/projects/VeNTeR/bowtie_alignment_%s.sam' % (bowtie_alignment_file, i))

                clean_up_tmp()



find_info_by_mapping('simulation_data/', int(sys.argv[1]))
