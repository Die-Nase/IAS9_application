import rdflib
from rdflib import Graph
from pyvis.network import Network

def visualize_graph(graph, hide_literals=False, hide_BNodes=False,
                    hide_labels=False, hide_type_nodes=False,
                    sparql_query="", physics=False):
    """
    Visualizes an RDFLib graph using PyVis, with options to filter nodes, edges, 
    and customize the visualization. The resulting interactive graph is displayed 
    as an IFrame and saved to an HTML file.

    Args:
        graph (rdflib.Graph): The RDFLib graph to visualize.
        hide_literals (bool): If True, hides nodes that are literals.
                              Information in literals is preserved in node titles.
        hide_BNodes (bool): If True, hides blank nodes (BNodes). 
                            Information in BNodes is preserved in node titles.
        hide_labels (bool): If True, hides labels on nodes and edges.
                            All information is available in the node titles.
        hide_type_nodes (bool): If True, hides nodes connected by the `rdf:type` predicate.
                                Type information is preserved in the node titles.
        sparql_query (str): A SPARQL query to extract a subgraph for visualization.
                            If empty, the entire graph is visualized.
        physics (bool): If True, enables physics simulation for the graph layout.

    Returns:
        IPython.core.display.IFrame: An IFrame displaying the interactive graph, 
                                     also saved as an HTML file.

    Notes:
        - The visualization is directed by default.
        - Nodes are color-coded based on their types and properties:
            - **Literals**: Yellow (#FFFF00)
            - **Blank Nodes**: Dark grey (#A9A9A9)
            - **schema:Organization**: Blue (#2196F3)
            - **schema:Person**: Green (#4CAF50)
            - **schema:SoftwareSourceCode**: Purple (#9C27B0)
            - **schema:CreativeWork**: Orange (#FF8800)
            - **Other URIs**: Light gray (#D3D3D3)
        - Even when hiding labels, literals, or type nodes, all associated information 
          is preserved in the node titles, which can be accessed by clicking on a node 
          in the interactive graph.
    """
    # Initialize a PyVis network
    g = Network(notebook=True, directed=True)
    
    # If a SPARQL query is provided, filter the graph and build a subgraph
    if sparql_query:
        subgraph = Graph()
        for row in graph.query(sparql_query):
            subgraph.add(row)  # Add each result to the subgraph
    else:
        subgraph = graph  # Use the full graph if no SPARQL query is provided
    
    # Fetch types and literals for nodes to enhance visualization details
    node_types = get_node_types(graph)
    node_literals = get_node_literals(graph)
    
    # Iterate over each triple in the subgraph
    for subject, predicate, obj in subgraph:
        # Optionally skip literal nodes
        if hide_literals and isinstance(obj, rdflib.Literal):
            continue
        
        # Optionally skip blank nodes (BNodes)
        if hide_BNodes:
            if isinstance(subject, rdflib.BNode) or isinstance(obj, rdflib.BNode):
                continue            
        
        # Optionally skip `rdf:type` edges
        if hide_type_nodes:
            if predicate == rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'):
                continue
        
        # Add subject and object nodes with labels, titles, and colors
        g.add_node(subject,
                   label=get_node_labels(subject, node_types, hide_labels),
                   title=get_title(subject, node_types, node_literals),
                   color=get_color(subject, node_types))
        g.add_node(obj,
                   label=get_node_labels(obj, node_types, hide_labels),
                   title=get_title(obj, node_types, node_literals),
                   color=get_color(obj, node_types))
        
        # Add edges with predicate labels
        if hide_labels:
            edge_label = ""  # Hide edge label if `hide_labels` is True
        else:
            edge_label = use_prefix(predicate)  # Use prefixes for predicate labels
        g.add_edge(subject, obj, label=edge_label,
                   title=get_title(predicate, node_types, node_literals))
        
        # Enable or disable physics simulation based on the `physics` argument
        g.toggle_physics(physics)
    
    # Display the graph in an interactive HTML file and return the file path
    return g.show("graph.html")


def get_node_labels(node, node_types, hide_labels):
    if hide_labels:
        return " "
    if isinstance(node, rdflib.BNode):
        return "BNode/type:" + use_prefix(node_types[str(node)])
    else:
        return use_prefix(node)

def get_node_types(graph):
    query = """
        SELECT ?node ?type WHERE { ?node a ?type }
    """

    node_types = {}
    for node, node_type in graph.query(query):
        node_types[str(node)] = str(node_type)
    return node_types

from rdflib import Graph, URIRef, BNode, Literal

def get_node_literals(graph):
    node_literals = {}

    for subject, predicate, obj in graph:
        if isinstance(obj, Literal):
            node_key = str(subject)
            if node_key not in node_literals:
                node_literals[node_key] = []
            node_literals[node_key].append((str(predicate), str(obj)))
        
        # # Handle case where the object is a node (URI or blank node) and the object itself has literals
        # if isinstance(obj, (URIRef, BNode)):
        #     for _, p, o in graph.triples((obj, None, None)):
        #         if isinstance(o, Literal):
        #             node_key = str(obj)
        #             if node_key not in node_literals:
        #                 node_literals[node_key] = []
        #             node_literals[node_key].append(str(o))
    
    # Remove duplicates from the lists of literals for each node
    for node in node_literals:
        node_literals[node] = list(set(node_literals[node]))

    return node_literals



def use_prefix(term):
    if "schema.org" in term:
        return "schema/"+str(term).split("schema.org/")[1]
    elif "ror.org" in term:
        return "ror/"+str(term).split("ror.org/")[1]
    
    elif term == rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'):
        return "w3/#type"
    else:
        return str(term)

def get_color(node, node_types):
    if isinstance(node, rdflib.Literal):
        return "#FFFF00" # Literal: yellow
    
    if isinstance(node, rdflib.BNode):
        return "#A9A9A9" # Blank Node: dark grey
    
    node_type = node_types.get(str(node))
    
    if node_type == "http://schema.org/Organization":
        return "#2196F3"  # Blue for schema:Organization
    
    if node_type == "http://schema.org/Person":
        return "#4CAF50"  # Green for schema:Person
    
    if node_type == "http://schema.org/SoftwareSourceCode":
        return "#9C27B0"  # Purple for schema:SoftwareSourceCode
    
    if node_type == "http://schema.org/CreativeWork":
        return "#FF8800"  # Orange for schema:CreativeWork
    
    return "#D3D3D3"  # Default: Light gray for other URIs

def get_title(node, node_types, node_literals):
    node_description = {}
    node_description["type"] = node_types.get(str(node), type(node))
    node_description["id"] = str(node)
    
    literals = node_literals.get(str(node), [])
    for predicate, literal in literals:
        node_description[use_prefix(predicate)] = str(literal)
    
    title = ""
    for key in node_description:
        title += f"{key}: {node_description[key]}\n"
        
    return title