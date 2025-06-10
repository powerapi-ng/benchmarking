import click
import pickle
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from adastop import MultipleAgentsComparator
LITTER_FILE = ".adastop_comparator.pkl"
def compare(ctx, input_file, n_groups, size_group, n_permutations, alpha, beta, seed, comparisons, compare_to_first):
    """
    Perform one step of adaptive stopping algorithm using csv file intput_file.
    The csv file must be of size `size_group`.
    At first call, the comparator will be initialized with the arguments passed and then it will be saved to a save file in `.adastop_comparator.pkl`.
    """
    path_lf = Path(input_file).parent.absolute() / LITTER_FILE
    df = pd.read_csv(input_file, index_col=0)

    assert len(df) == size_group , "The csv file does not contain the right number of scores. If must constain `size_group` scores. Either change the argument `size_group` or give a csv file with {} scores".format(size_group)
    
    n_fits_per_group = len(df) 
    n_agents = len(df.columns)

    if compare_to_first:
        comparisons = [(0,i) for i in range(1, n_agents)]
    else:
        comparisons = None

    # if this is not first group, load data for comparator.
    if os.path.isfile(path_lf):
        with open(path_lf, 'rb') as fp:
            comparator = pickle.load(fp)

        names = []
        for i in range(len(comparator.agent_names)):
            if i in comparator.current_comparisons.ravel():
                names.append(comparator.agent_names[i])


        Z = [np.hstack([comparator.eval_values[agent], df[agent]]) for agent in names]
        if len(Z[0]) > comparator.K * n_fits_per_group:
            raise ValueError('Error: you tried to use more group than what was initially declared, this is not allowed by the theory.')
        assert "continue" in list(comparator.decisions.values()), "Test finished at last iteration."

    else:
        comparator = MultipleAgentsComparator(n=n_fits_per_group, K=n_groups,
                                              B=n_permutations, comparisons=comparisons,
                                              alpha=alpha, beta=beta, seed=seed)
        names = df.columns

        Z = [df[agent].values for agent in names]

    data = {names[i] : Z[i] for i in range(len(names))}
    # recover also the data of agent that were decided.
    if comparator.agent_names is not None:
        for agent in comparator.agent_names:
            if agent not in data.keys():
                data[agent]=comparator.eval_values[agent]

    comparator.partial_compare(data, False)
    if not("continue" in list(comparator.decisions.values())):
        click.echo('')
        click.echo("Test is finished, decisions are")
        click.echo(comparator.get_results().to_markdown())
        
    else:
        still_here = []
        for c in comparator.comparisons:
            if comparator.decisions[str(c)] == "continue":
                still_here.append( comparator.agent_names[c[0]])
                still_here.append( comparator.agent_names[c[1]])
        still_here = np.unique(still_here)
        click.echo("Still undecided about "+" ".join(still_here))
    click.echo('') 
    
    with open(path_lf, 'wb') as fp:
        pickle.dump(comparator, fp)
        click.echo("Comparator Saved")

compare(ctx=None, input_file='test_csv_domains_1.csv', n_groups=4, size_group=4, n_permutations=0, alpha=0.01, beta=0, comparisons=[(0,3), (1,4), (2,5), (8,6), (9,7)], seed=None, compare_to_first=False)
compare(ctx=None, input_file='test_csv_domains_2.csv', n_groups=4, size_group=4, n_permutations=0, alpha=0.01, beta=0, comparisons=[(0,3), (1,4), (2,5), (8,6), (9,7)], seed=None, compare_to_first=False)
compare(ctx=None, input_file='test_csv_domains_3.csv', n_groups=4, size_group=4, n_permutations=0, alpha=0.01, beta=0, comparisons=[(0,3), (1,4), (2,5), (8,6), (9,7)], seed=None, compare_to_first=False)
compare(ctx=None, input_file='test_csv_domains_4.csv', n_groups=4, size_group=4, n_permutations=0, alpha=0.01, beta=0, comparisons=[(0,3), (1,4), (2,5), (8,6), (9,7)], seed=None, compare_to_first=False)
