#!/bin/bash

# Dossier contenant les fichiers CSV
dossier=$1

find "$dossier" -type f -name "vjoule*.csv" | while read -r fichier; do
    nb_core=$(echo $fichier | tr "_" "\n" | tail -2 | paste -sd "," | cut -d"." -f1 | cut -d"," -f1)
    nb_ops_per_core=$(echo $fichier | tr "_" "\n" | tail -2 | paste -sd "," | cut -d"." -f1 | cut -d"," -f2)

    if ! grep -q "energy_cores,energy_pkg,energy_ram,nb_core,nb_ops_per_core,iteration" "$fichier"; then
        awk -F, -v nb_core="$nb_core" -v nb_ops_per_core="$nb_ops_per_core" '
        NR==1 {print "energy_cores,energy_pkg,energy_ram,nb_core,nb_ops_per_core,iteration"; next}
        {
            if ($1 == "CPU") {
                if ($2 < 100) {
                    cpu[$3] = 1000*$2
                } else {
                    cpu[$3] = $2
                }
            } else if ($1 == "RAM") {
                ram[$3] = $2
            }
        }
        END {
            for (i in cpu) {
                print cpu[i] ",0.0," ram[i] "," nb_core "," nb_ops_per_core "," i
            }
        }
        ' OFS=, "$fichier" > tmp_file && mv tmp_file "$fichier"
    fi
done
