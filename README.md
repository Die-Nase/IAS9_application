# **IAS9 Application Lucas Lamparter**

## **Overview**
This project builds a semantically rich RDF graph from a GitHub organization, linking repositories and contributors using schema.org standards. Data from GitHub, ORCID, ROR and WikiData APIs are integrated to create a graph representation of:

- **schema.org:Person**: Representing contributors.
- **schema.org:Organization**: Representing the hosting organization.
- **schema.org:SoftwareSourceCode**: Representing repositories.

The resulting graph is visualized via PyVis

---

## **Installation**

### **Prerequisites**
Ensure you have the following installed:

- **Python** (>=3.8): [Download Python](https://www.python.org/downloads/)
- Required Python libraries (install via `pip`):
  ```bash
  pip install rdflib requests pyvis
  ```

### **Clone the Repository**
```bash
git clone https://github.com/Die-Nase/IAS9_application.git
cd IAS9_application
```

---

## **Usage**

### **1. Setup API Tokens**
You need valid API tokens for GitHub and ORCID to fetch data.

- **GitHub Token**: Generate at [GitHub Developer Settings](https://github.com/settings/tokens).
- **ORCID Token**: Obtain from [ORCID API](https://orcid.org/).


### **2. Build the Graph**
Use the `build_graph_from_github_org` function to create an RDF graph:

```python
from utils import build_graph_from_github_org

# Define inputs
github_org_name = "Materials-Data-Science-and-Informatics"
corresponding_ror_id = "https://ror.org/02nv7yv05"
github_token = "your_github_token"
orcid_token = "your_orcid_token"

# Build the graph
graph = build_graph_from_github_org(github_org_name, corresponding_ror_id, github_token, orcid_token)

# Save the graph to a file
graph.serialize("graph.ttl")
```

**Run main.py to build a graph as described above or use the 'interactive_build_and_query.ipynb' notebook (recommended) for interactive building and visualization of the graph.**

### **3. Visualize the Graph**
For PyVis visualization:

```python
from visualizer import visualize_graph

visualize_graph(graph)
```
**Use the 'interactive_build_and_query.ipynb' notebook for visualizing the graph.**

---

## **Project Structure**
```
IAS9_application_LucasLamparter/
├── interactive_build_and_query.ipynb.py        # interactive graph buidling and visualization (recommended)
├── main.py         # alternative script that builds and saves the graph from github
├── utils.py        # Contains building, fetching and other utility functions
├── mappers.py      # Contains schema.org mappers
├── visualizer.py   # Contains 'visualize_graph' and related functions
├── app.log         # log file of the graph building process
├── graph.html      # latest pyvis visualization triggered from the notebook
├── graph.ttl       # saved graphed (by notebook or script)
├── README.md       # Project documentation
```

---


## **License**
This project is licensed under the MIT License. See `LICENSE` for details.

---

