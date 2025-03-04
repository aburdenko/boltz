#! /usr/bin/bash
rm -rf boltz_results_ligand
sudo mount -o remount,size=8G /dev/shm
boltz predict ./examples/ligand.fasta #--use_msa_server
