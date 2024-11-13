tar -cJf {{ results_directory }}.tar.xz {{ results_directory }} && rm -rf {{ results_directory }}
md5sum {{ results_directory }}.tar.xz  > {{ results_directory }}.tar.xz.md5
