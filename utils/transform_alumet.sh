#!/bin/bash

dossier=$1

find "$dossier" -type f -regex ".*/alumet_.*_[0-9]+_[0-9]+\.csv" | while read -r fichier; do
    nb_core=$(echo $fichier | cut -d'_' -f4)
    nb_ops_per_core=$(echo $fichier | cut -d'_' -f5 | cut -d'.' -f1)

    if ! grep -q "energy_cores,energy_pkg,energy_ram,nb_core,nb_ops_per_core,iteration" "$fichier"; then
        awk -F, -v nb_core="$nb_core" -v nb_ops_per_core="$nb_ops_per_core" '
        NR==1 {print "energy_cores,energy_pkg,energy_ram,nb_core,nb_ops_per_core,iteration"; next}
        {
            if ($1 == "cores") {
                cores[$3] += $2
            } else if ($1 == "dram") {
                ram[$3] += $2
            } else if ($1 == "package") {
                pkg[$3] += $2
            }
        }
        END {
            for (i in pkg) {
                print cores[i] "," pkg[i] "," ram[i] "," nb_core "," nb_ops_per_core "," i
            }
        }
        ' OFS=, "$fichier" > tmp_file && mv tmp_file "$fichier"
    fi
done

