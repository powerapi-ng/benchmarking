import visualization


def os_comparison_boxplots_processor_versions_pkg_all(dfs, save=False, show=False):
    visualization.plot_boxplots(
        dfs,
        "processor_detail",
        "pkg_coefficient_of_variation",
        "job",
        "All Measurements",
    )

def os_comparison_boxplots_processor_versions_ram_all(dfs, save=False, show=False):
    visualization.plot_boxplots(
        dfs,
        "processor_detail",
        "ram_coefficient_of_variation",
        "job",
        "All Measurements",
        )
 

def os_comparison_heatmap_processor_versions_pkg_nb_ops(joined_df, tool, save=False, show=False):
    visualization.plot_os_degradation_nb_ops(joined_df, "pkg", tool)

def os_comparison_heatmap_processor_versions_ram_nb_ops(joined_df, tool, save=False, show=False):
    visualization.plot_os_degradation_nb_ops(joined_df, "ram", tool)

def os_comparison_heatmap_processor_versions_pkg_percent_used(joined_df, save=False, show=False):
    visualization.plot_os_degradation_percent_used(joined_df, "pkg")

def os_comparison_heatmap_processor_versions_ram_percent_used(joined_df, save=False, show=False):
    visualization.plot_os_degradation_percent_used(joined_df, "ram")

def debian_facetgrid_processor_versions_pkg_cv_nb_ops(debian_df, save=True, show=True):
    visualization.plot_facet_grid_nb_ops_per_core_versions_domain_cv(debian_df, "pkg", "debian11 5.10")
def debian_facetgrid_processor_versions_ram_cv_nb_ops(debian_df, save=True, show=True):
    visualization.plot_facet_grid_nb_ops_per_core_versions_domain_cv(debian_df, "ram", "debian11 5.10")
def ubuntu_facetgrid_processor_versions_pkg_cv_nb_ops(ubuntu_df, save=True, show=True):
    visualization.plot_facet_grid_nb_ops_per_core_versions_domain_cv(ubuntu_df, "pkg", "ubuntu2404 6.8")
def ubuntu_facetgrid_processor_versions_ram_cv_nb_ops(ubuntu_df, save=True, show=True):
    visualization.plot_facet_grid_nb_ops_per_core_versions_domain_cv(ubuntu_df, "ram", "ubuntu2404 6.8")
