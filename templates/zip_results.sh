cd {{ results_directory }}/..
tar -cJf /home/{{ g5k_username }}/{{ results_directory }}.tar.xz /home/{{ g5k_username }}/{{ results_directory }}
cd /home/{{ g5k_username }}
rm -rf {{ results_directory }}
md5sum {{ results_directory }}.tar.xz  > {{ results_directory }}.tar.xz.md5
