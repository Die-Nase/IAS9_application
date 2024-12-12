from utils import build_graph_from_github_org
from visualizer import visualize_graph

# provide authentification tokens for github api and orcid public api
github_token = "your-github-token"
orcid_token = "your-orcid-token"

# Provide the Name of the Github Organization and the corresponding ROR ID
github_org_name = "Materials-Data-Science-and-Informatics"
corresponding_ror_id = "02nv7yv05"

if __name__ == "__main__":
    # build graph
    graph = build_graph_from_github_org(github_org_name, corresponding_ror_id,
                                        github_token, orcid_token)
    # save graph
    graph.serialize(destination="graph.ttl")