import logging
from logging.handlers import RotatingFileHandler
import requests
from mappers import *
from rdflib import Graph
from rdflib.extras.external_graph_libs import rdflib_to_networkx_graph
from pyvis.network import Network

def build_graph_from_github_org(github_org_name, corresponding_ror_id, github_token, orcid_token):
    """
    Builds an RDF graph representing a GitHub organization's repositories and contributors, 
    enriched with data from ORCID and ROR APIs. 

    Args:
        github_org_name (str): The GitHub organization name (e.g., "Materials-Data-Science-and-Informatics").
        corresponding_ror_id (str): The ROR (Research Organization Registry) identifier for the organization 
                                    (e.g., "https://ror.org/02nv7yv05").
        github_token (str): GitHub API access token for authenticating API requests.
        orcid_token (str): ORCID API access token for authenticating API requests.

    Returns:
        rdflib.Graph: An RDF graph containing information about the organization, its repositories, 
                      and contributors, represented in schema.org format.

    Notes:
        - The graph integrates data from GitHub, ORCID, ROR, and WikiData
        - The main entities in the graph are:
            - `schema.org:Person`: Representing individual contributors.
            - `schema.org:Organization`: Representing the organization hosting the repositories,
               as well as the 'affiliation' and 'alumniOf' of `schema.org:Person`.
            - `schema.org:SoftwareSourceCode`: Representing individual repositories.
        - Only contributors with an associated ORCID record are included in the graph.
        - Only organizations with an associated ROR ID record are included in the graph.
    """
    # Initialize a logger for tracking the function's operations
    logger = get_logger(name="build_graph_logs", overwrite=True)
    logger.info(f"Starting the process to build an RDF graph for the GitHub organization: {github_org_name}.")

    # Initialize an RDFLib graph
    graph = Graph()

    # Step 1: Fetch and add the organization data from ROR to the graph
    logger.info(f"Fetching organization data from ROR for ID: {corresponding_ror_id}")
    org = fetch_schema_org_organization_from_ror(corresponding_ror_id, logger)
    graph.parse(data=org, format="json-ld")

    # Step 2: Fetch GitHub organization details
    logger.info(f"Fetching GitHub organization details for: {github_org_name}")
    github_org = fetch_github_org(github_org_name, github_token, logger)
    
    # Step 3: Fetch the repositories associated with the GitHub organization
    logger.info(f"Fetching repositories for the organization: {github_org_name}")
    repos = fetch_github_repos(github_org["repos_url"], github_token, logger)
    logger.info(f"Found {len(repos)} repositories for the organization.")

    for repo in repos[:1]:
        # Step 4: Convert the repository data to schema.org SoftwareSourceCode format
        logger.info(f"Processing repository: {repo.get('name', 'Unknown Name')}")
        source_code = github_repo_to_SoftwareSourceCode(repo)
        source_code["sourceOrganisation"] = org  # Link the repository to the organization
        source_code["contributor"] = []  # Initialize an empty list for contributors
        
        # Step 5: Fetch contributors for the current repository
        contributors = fetch_github_contributors(repo["contributors_url"], github_token, logger)
        logger.info(f"Found {len(contributors)} contributors for the repository: {repo.get('name', 'Unknown Name')}")
        
        for contributor in contributors:
            # Fetch GitHub user details for the contributor
            user = fetch_github_user(contributor["url"], github_token, logger)
            
            # Skip contributors without a proper name to avoid random orcids showing up in the graph
            if not user["name"] or user["name"] == user["login"]:
                logger.warning(f"Skipping contributor with no valid name: {user.get('login', 'Unknown Login')}")
                continue
            
            # Step 6: Attempt to find the contributor's ORCID ID using their name
            logger.info(f"Looking up ORCID for contributor: {user['name']}")
            orcid = orcid_lookup(user["name"], orcid_token, logger)
            if not orcid:
                logger.warning(f"No ORCID found for contributor: {user['name']}")
                continue  # Skip contributors without an ORCID ID
            
            # Step 7: Fetch the ORCID record for the contributor
            logger.info(f"Fetching ORCID data for: {user['name']} ({orcid})")
            person = fetch_orcid_person(orcid, orcid_token, logger, accept_header="ld+json")
            
            # Step 8: Try to find ROR IDs for all organizations listed in person.
            # If org has ROR ID -> ROR ID is returned
            # If org has GRID ID -> ROR API is fetched for the corresponding ROR ID
            # If org has RINGGOLD ID -> WikiData is fetched for the corresponding ROR ID if available
            # Organizations without ROR ID are excluded from the graph
            logger.info(f"Updating organization data for contributor: {user['name']}")
            person = update_person_organizations_with_ror(person, logger)
            
            # Add the contributor's enriched data to the graph
            graph.parse(data=person, format="json-ld")
            logger.info(f"Contributor {user['name']} added to the graph.")
            
            # Link the contributor to the current repository
            source_code["contributor"].append(person)
        
        # Add the repository (SoftwareSourceCode) to the graph
        graph.parse(data=source_code, format="json-ld")
        logger.info(f"Repository {repo.get('name', 'Unknown Name')} added to the graph.")
    
    logger.info("Graph building process completed successfully.")
    # Return the constructed RDF graph
    return graph


# def build_graph_from_github_org(github_org_name, corresponding_ror_id, github_token, orcid_token):
#     logger = get_logger(name = "build_graph logs", overwrite = True)

#     graph = Graph()
#     org = fetch_schema_org_organization_from_ror(corresponding_ror_id, logger)
#     graph.parse(data=org ,format="json-ld")
    
#     github_org = fetch_github_org(github_org_name, github_token, logger)
#     repos = fetch_github_repos(github_org["repos_url"], github_token, logger)
#     for repo in repos:
#         source_code = github_repo_to_SoftwareSourceCode(repo)
#         source_code["sourceOrganisation"] = org
#         source_code["contributor"] = []
#         contributors = fetch_github_contributors(repo["contributors_url"], github_token, logger)
#         for contributor in contributors:
#             user = fetch_github_user(contributor["url"], github_token, logger)
#             if not user["name"] or user["name"]==user["login"]:
#                 continue
#             orcid = orcid_lookup(user["name"], orcid_token, logger)
#             if not orcid:
#                 continue
#             person = fetch_orcid_person(orcid, orcid_token, logger, accept_header="ld+json")
#             person = update_person_organizations_with_ror(person, logger)
#             graph.parse(data=person, format="json-ld")
#             source_code["contributor"].append(person)
#         graph.parse(data=source_code,format="json-ld")
    
#     return graph

def get_logger(name="app_logger", log_file="app.log", level=logging.DEBUG, overwrite=False):
    
    # Create a logger with the given name
    logger = logging.getLogger(name)
    
    # If logger has already been created, avoid adding handlers again
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(level)
    
    # Determine file handler behavior based on 'overwrite' argument
    if overwrite:
        file_handler = logging.FileHandler(log_file, mode='w',  encoding='utf-8')  # Overwrite file
    else:
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5,  encoding='utf-8')  # Append with rotation
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    # Define the log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Attach the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def hide_token(headers):
    sanitized_headers = headers.copy()
    if 'Authorization' in sanitized_headers:
        sanitized_headers['Authorization'] = '***HIDDEN***'  # Mask the token
    return sanitized_headers


def fetch(base_url, headers, logger, **kwargs):
    try:
        logger.info(f"Starting request to {base_url} with headers: {hide_token(headers)}")
        response = requests.get(base_url, headers=headers, **kwargs)
        
        if response.status_code == 200:
            logger.info(f"Successfully fetched data from {base_url} (Status: {response.status_code})")
            return response.json() 
        
        logger.warning(f"Request to {base_url} returned status {response.status_code}")
        response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to {base_url} failed due to: {e}")
        return None
    
def fetch_github_org(org_name, token, logger):
    headers = {"Authorization": f"token {token}"}
    base_url = f"https://api.github.com/orgs/{org_name}"
    
    return fetch(base_url, headers, logger=logger)

def fetch_github_repos(repos_url, token, logger):
    headers = {"Authorization": f"token {token}"}
    return fetch(repos_url, headers, logger=logger)

def fetch_github_contributors(contributors_url, token, logger):
    headers = {"Authorization": f"token {token}"}
    return fetch(contributors_url, headers, logger=logger)

def fetch_github_user(user_url, token, logger):
    headers = {"Authorization": f"token {token}"}
    return fetch(user_url, headers=headers, logger=logger)

def orcid_lookup(name, orcid_token, logger):
    base_url = "https://pub.orcid.org/v3.0/"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {orcid_token}"}
    
    family_name = name.split()[-1]
    given_names = name.split(" "+family_name)[0]
    query = f'given-names:{given_names}+AND+family-name:{family_name}'
    
    query_url = f"{base_url}search/?q={query}"
    
    response_json = fetch(query_url, headers, logger=logger)
    
    if response_json["result"]:
        return response_json["result"][0].get("orcid-identifier", {}).get("path", None) #take first result
    return None
    

def fetch_orcid_person(orcid, orcid_token, logger, accept_header="ld+json"):
    base_url = f"https://pub.orcid.org/v3.0/{orcid}"
    headers = {"Accept": f"application/{accept_header}", "Authorization": f"Bearer {orcid_token}"}
    return fetch(base_url, headers, logger=logger)

def get_ror_from_grid(grid, logger):
    base_url = f"https://api.ror.org/organizations?query=%22{grid}%22"
    logger.info(f"Starting ROR lookup for GRID: {grid}")
    
    ror_results = fetch(base_url, {}, logger)
    
    if not ror_results:
        logger.error(f"Failed to fetch ROR records for GRID: {grid}. Response was None or invalid.")
        return None
    
    n_results = ror_results.get("number_of_results", 0)
    items = ror_results.get("items", [])
    
    if n_results == 0:
        logger.warning(f"No ROR records found for GRID: {grid}.")
        return None
    
    # Get first ROR ID
    ror = items[0].get("id", None)
    if not ror:
        logger.error(f"Missing 'id' in ROR API response for GRID: {grid}. Response: {ror_results}")
        return None
    
    if n_results == 1:
        logger.info(f"Successfully found 1 ROR record for GRID: {grid} -> ROR: {ror}")
    else:
        logger.warning(f"Multiple ROR records found for GRID: {grid}. Using first ROR: {ror}")
    
    return ror

def get_ror_from_ringgold(ringgold_id, logger):
    # SPARQL query to fetch the ROR ID from Wikidata using the Ringgold ID
    sparql_query = f"""
    SELECT ?ror_id WHERE {{
      ?org wdt:P3500 "{ringgold_id}" .  # Match the organization with the given Ringgold ID (P3500)
      ?org wdt:P6782 ?ror_id .           # Get the corresponding ROR ID (P6782)
    }}
    """
    
    # Wikidata Query Service endpoint
    endpoint_url = "https://query.wikidata.org/sparql"
    
    headers = {
        "User-Agent": "Python script to query Wikidata for ROR using Ringgold",
        "Accept": "application/json"
    }
    logger.info(f"Starting query for Ringgold ID {ringgold_id} in Wikidata.")
    response = fetch(endpoint_url, headers, logger, params={"query": sparql_query, "format": "json"})
    
    results = response.get('results', {}).get('bindings', [])
    if not results:
        logger.info(f"No ROR ID found for Ringgold ID {ringgold_id}.")
        return None
        
    ror_id = "https://ror.org/"+results[0]['ror_id']['value']  # Extract the ROR ID from the SPARQL result
    logger.info(f"Found ROR ID {ror_id} for Ringgold ID {ringgold_id}.")
    return ror_id

def get_ror_from_organization(org, logger):  
    logger.info(f"Starting to extract ROR for the organization: {org.get('name', 'Unnamed Organization')}")

    # Step 1: Check if @id is a ROR URL
    org_id = org.get('@id')
    if org_id:
        logger.info(f"Found @id: {org_id}")
        if "ror.org" in org_id:
            logger.info(f"@id is already a ROR identifier: {org_id}")
            return org_id
        elif "grid" in org_id:
            logger.info(f"@id is a GRID identifier: {org_id}")
            ror_id = get_ror_from_grid(org_id, logger)
            if ror_id:
                return ror_id

    # Step 2: Check for identifier
    identifier = org.get('identifier')
    if identifier:
        logger.info(f"Found identifier: {identifier}")
        
        if isinstance(identifier, list):
            for id_obj in identifier:
                ror = process_identifier(id_obj, logger)
                if ror:
                    return ror
                
        elif isinstance(identifier, dict):
            ror = process_identifier(identifier, logger)
            if ror:
                return ror
    
    # If no ROR was found
    logger.info("No ROR could be determined for this organization.")
    return None

def process_identifier(identifier, logger):
    property_id = identifier.get('propertyID')
    value = identifier.get('value')

    logger.info(f"Processing identifier with propertyID: {property_id}, value: {value}")

    # Check if the propertyID corresponds to a ROR
    if property_id.lower() == 'ror':
        logger.info(f"Identifier is a ROR: {value}")
        return value
    
    # Check if the propertyID corresponds to a Ringgold ID
    if property_id.lower() == 'ringgold':
        logger.info(f"Identifier is a Ringgold identifier. Querying ROR for Ringgold: {value}")
        ror_id = get_ror_from_ringgold(value, logger)
        if ror_id:
            return ror_id

    logger.info(f"PropertyID {property_id} is not recognized as ROR or Ringgold.")
    return None

def fetch_schema_org_organization_from_ror(ror_id, logger):
    
    # Remove the URL part if the ROR ID is a full URL
    if ror_id.startswith("https://ror.org/"):
        ror_id = ror_id.split('/')[-1]
    
    base_url = f"https://api.ror.org/organizations/{ror_id}"
    headers = {"Accept": "application/json"}
    
    logger.info(f"Starting query to ROR API for ROR ID: {ror_id}")
    
    ror_data = fetch(base_url, headers, logger)
    if not ror_data:
        logger.error(f"Failed to fetch ROR data for ROR ID: {ror_id}.")
    logger.info(f"Successfully fetched ROR data for ROR ID: {ror_id}")
    return ror_org_to_schema_org(ror_data)

def update_person_organizations_with_ror(person, logger):
    person = dict(person)
    for key in ["alumniOf", "affiliation"]:
        if key in person:
            organizations = person[key]
            
            # Ensure the property is a list (it can be a single dict too in schema.org)
            if isinstance(organizations, dict): 
                organizations = [organizations] 
            
            updated_organizations = []
            
            for org in organizations:
                ror_id = get_ror_from_organization(org, logger)
                if ror_id:
                    updated_organizations.append({
                        '@type': 'Organization',
                        '@id': ror_id
                    })
                else:
                    print(f"Organization {org.get('@id', 'Unknown')} could not be resolved to a ROR ID and will be removed.")
            
            if updated_organizations:
                person[key] = updated_organizations
            else:
                del person[key]  # Remove the key if no valid organizations remain
    
    return person

