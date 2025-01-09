cd {{ results_directory }}/..
tar -cJf /home/nleblond/{{ results_directory }}.tar.xz /home/nleblond/{{ results_directory }}
cd /home/nleblond
rm -rf {{ results_directory }}
md5sum {{ results_directory }}.tar.xz  > {{ results_directory }}.tar.xz.md5
