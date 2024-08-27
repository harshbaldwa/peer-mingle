import networkx as nx
import random


def sample_pool_choosing(reviewers_all, i, p, used):
    sample_pool = reviewers_all[used].copy()

    if i in sample_pool:
        sample_pool.remove(i)

    if len(sample_pool) < p:
        return sample_pool + sample_pool_choosing(
            reviewers_all, i, p - len(sample_pool), used + 1)
    else:
        return random.sample(sample_pool, p)


def create_regular_graph(n, p):
    out_degree_correctness = False
    in_degree_correctness = False

    while not out_degree_correctness or not in_degree_correctness:
        G = nx.DiGraph()

        for i in range(n):
            G.add_node(i)

        reviewers_all = list(list() for _ in range(p))
        reviewers_all[0] = list(range(n))

        try:
            for i in range(n):
                reviewers = sample_pool_choosing(reviewers_all, i, p, 0)
                for reviewer in reviewers:
                    G.add_edge(reviewer, i)
                    for j in range(p):
                        if reviewer in reviewers_all[j]:
                            reviewers_all[j].remove(reviewer)
                            if j < p - 1:
                                reviewers_all[j + 1].append(reviewer)
                            break

            out_degrees = [G.out_degree(i) == p for i in range(n)]
            in_degrees = [G.in_degree(i) == p for i in range(n)]
        except IndexError:
            continue

        out_degree_correctness = all(out_degrees)
        in_degree_correctness = all(in_degrees)

    return G
