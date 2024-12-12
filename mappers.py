
def ror_org_to_schema_org(ror_data):
    schema_org_organization = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": ror_data.get('id', None),  # ROR ID (unique identifier for the organization)
        "name": ror_data.get('name', None),
        "alternateName": ror_data.get('aliases', []),  # Aliases or alternative names
        "sameAs": [link for link in ror_data.get('links', [])],  # Official links (like website, social media)
        "address": {
            "@type": "PostalAddress",
            "addressLocality": ror_data.get('addresses', [{}])[0].get('city', None),
            "addressRegion": ror_data.get('addresses', [{}])[0].get('state', None),
            "addressCountry": ror_data.get('addresses', [{}])[0].get('country', None)
        },
        "identifier": [
            {
                "@type": "PropertyValue",
                "propertyID": "ROR",
                "value": ror_data.get('id', None).split('/')[-1]  # Extract ROR identifier (without URL)
            }
        ],
    }
    
    external_ids = ror_data.get('external_ids', {})
        
    if 'GRID' in external_ids:
        schema_org_organization['identifier'].append({
            "@type": "PropertyValue",
            "propertyID": "GRID",
            "value": external_ids['GRID']['preferred']
        })

    if 'ISNI' in external_ids:
        schema_org_organization['identifier'].append({
            "@type": "PropertyValue",
            "propertyID": "ISNI",
            "value": external_ids['ISNI']['preferred']
        })

    if 'Wikidata' in external_ids:
        schema_org_organization['identifier'].append({
            "@type": "PropertyValue",
            "propertyID": "Wikidata",
            "value": external_ids['Wikidata']['preferred']
            })
        
    return schema_org_organization

def github_repo_to_SoftwareSourceCode(github_repo):
    source_code = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "@id": f"https://api.github.com/repositories/{github_repo['id']}",
        "name": github_repo.get("name"),
        "description": github_repo.get("name"),
        "codeRepository": github_repo.get("url"),
    }
    return source_code

