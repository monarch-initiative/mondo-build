#!/usr/bin/env python3

from pathlib import Path
import yaml
import re
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
mkdocs_file = ROOT / "mkdocs.yml"
pattern_files = (ROOT / "src/patterns/dosdp-patterns").glob("*.yaml")
pattern_doc_dir = ROOT / "docs/editors-guide/patterns"
sample_data_dir = ROOT / "src/patterns/data/matches"
pattern_matches_location_raw = "https://raw.githubusercontent.com/monarch-initiative/mondo/master/src/patterns/data/matches"
pattern_matches_location_gh = "https://github.com/monarch-initiative/mondo/blob/master/src/patterns/data/matches"


def curie_to_uri(curie):
    prefix, identifier = curie.split(":")
    if prefix == 'owl':
        return f"http://www.w3.org/2002/07/owl#{identifier}"
    else:
        return f"http://purl.obolibrary.org/obo/{prefix}_{identifier}"


def curie_to_link(curie):
    return f"[{curie}]({curie_to_uri(curie)})"


def is_curie(s):
    return ":" in s


def render_var(var, mapping):
    var_str = mapping[var]
    if is_curie(var_str):
        return  f"{var}\({curie_to_link(var_str)}\)"
    # check format ''class''
    p = re.compile(r"'[^']*'")
    if p.match(var_str):
        link_str = re.sub(r"'([^']*)'", lambda m: curie_to_link(pattern["classes"][m.group(1)]), var_str)
    else:
        link_str = curie_to_link(pattern["classes"][var_str])

    return f"{var}\({link_str}\)"


def render_equivalent(text, vars, pattern):
    ret = text % tuple("{" + render_var(var, pattern["vars"]) + "}" for var in vars)
    mapping = {}
    mapping.update(pattern["classes"])
    mapping.update(pattern["relations"])
    p = re.compile(r"'[^']*'")
    ret = re.sub(r"'([^']*)'", lambda m: "{" + m.group(1) + "\(" + curie_to_link(mapping[m.group(1)]) + "\)}", ret)
    return ret


def render_name(text, vars, pattern):
    ret = text % tuple("{" + render_var(var, pattern["vars"]) + "}" for var in vars)
    return ret 


# We might need to make changes to the mkdocs.yaml file
# mkdocs_yaml = yaml.load(mkdocs_file.read_text(), Loader=yaml.FullLoader)

pattern_lst = []

for pattern_file in pattern_files:
    print(pattern_file)
    pattern = yaml.load(pattern_file.read_text(), Loader=yaml.FullLoader)
    md_file_path = pattern_doc_dir / (pattern_file.stem + ".md")
    with md_file_path.open("w") as fout:
        fout.write(f"# {pattern['pattern_name']} \n\n")
        fout.write(f"[{pattern['pattern_iri']}]({pattern['pattern_iri']})\n")
        fout.write("## Description \n\n")
        fout.write(pattern["description"] + "\n")
        if "contributors" in pattern:
            fout.write("## Contributors \n")
            for contributor in pattern["contributors"]:
                fout.write(f"* [{contributor}]({contributor}) \n")
        if "name" in pattern:
            fout.write("## Name \n\n")
            fout.write(render_name(pattern["name"]["text"], pattern["name"]["vars"], pattern))
            fout.write("\n\n")
        if "annotations" in pattern:
            fout.write("## Annotations \n\n")
            for anno in pattern["annotations"]:
                fout.write("* ")
                fout.write(f"annotation: {render_var(anno['annotationProperty'], pattern['annotationProperties'])}  \n")
                fout.write("text: " + render_name(anno["text"], anno["vars"], pattern))
                fout.write("\n\n")
        if "def" in pattern: 
            fout.write("## Definition \n\n")
            fout.write(render_name(pattern["def"]["text"], pattern["def"]["vars"], pattern))
            fout.write("\n\n")
        if "equivalentTo" in pattern:
            fout.write("## Equivalent to \n\n")
            fout.write(render_equivalent(pattern["equivalentTo"]["text"], pattern["equivalentTo"]["vars"], pattern))
            fout.write("\n\n")

        # Create sample table
        tsv_file = sample_data_dir / (pattern_file.stem + ".tsv")
        if tsv_file.is_file():
            examples = []
            try:
                df = pd.read_csv(tsv_file, sep="\t")
                ghurl = f"{pattern_matches_location_gh}/{pattern_file.stem}.tsv"
                if not df.empty:
                    examples.append('[mondo]({})'.format(ghurl))
                    example = ghurl
                    dfh = df.head()
                    sample_table = dfh.to_markdown(index=False)
                    fout.write("## Data preview: \n")
                    oboiri="http://purl.obolibrary.org/obo/"
                    fout.write(sample_table.replace(oboiri,"").replace("_",":"))
                    fout.write("\n\n")
                    fout.write(f"See full table [here]({example}) \n")
                else:
                    print("No matches!")
            except Exception as e:
                print("Error processing the tsv file!", e)
        else:
            print(str(tsv_file) + " does not exist!")
    pattern_lst.append((pattern_file.stem, pattern))

# create the index.md file 
pattern_lst.sort(key=lambda x: x[1]['pattern_name'].lower())
index_md_path = pattern_doc_dir / "index.md"
with index_md_path.open("w") as fout:
    fout.write(f"# Design Patterns \n\n")
    fout.write(f"\n")
    for pattern_file_name, pattern in pattern_lst:        
        fout.write(f"* [{pattern['pattern_name']}]({pattern_file_name}/) \n")



