import os
import ast
import json
import argparse
import networkx as nx

class KnowledgeGraph:
    def __init__(self):
        # Create a directed graph for capturing directional relationships.
        self.graph = nx.DiGraph()

    def add_fact(self, subject, relation, obj):
        """
        Add a fact to the knowledge graph in the form:
            subject --relation--> obj.
        """
        self.graph.add_node(subject)
        self.graph.add_node(obj)
        self.graph.add_edge(subject, obj, relation=relation)

    def query_fact(self, subject, relation):
        """
        Forward query: Given a subject and a relation, return all objects.
        """
        if subject not in self.graph:
            return []
        return [
            target for _, target, data in self.graph.out_edges(subject, data=True)
            if data.get('relation') == relation
        ]

    def query_fact_reverse(self, obj, relation):
        """
        Reverse query: Given an object and a relation, return all subjects.
        """
        if obj not in self.graph:
            return []
        return [
            source for source, _, data in self.graph.in_edges(obj, data=True)
            if data.get('relation') == relation
        ]

    def display_facts(self):
        """
        Return a list of strings representing every fact in the graph.
        """
        facts = []
        for subject, obj, data in self.graph.edges(data=True):
            rel = data.get('relation', 'is_related_to')
            facts.append(f"{subject} {rel} {obj}")
        return facts

def load_sku_files(sku_folder, kg):
    """
    Scan the given SKU folder and load all files ending with .sku.
    Each file is expected to contain one triple per line, e.g.:
        ("Hypertension", "treated_by", "ACE Inhibitor")
    """
    if not os.path.isdir(sku_folder):
        print(f"SKU folder '{sku_folder}' does not exist. Skipping SKU import.")
        return

    for filename in os.listdir(sku_folder):
        if not filename.lower().endswith('.sku'):
            continue  # Skip files that are not .sku
        filepath = os.path.join(sku_folder, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            # Safely parse the triple using ast.literal_eval
                            fact = ast.literal_eval(line)
                            if isinstance(fact, tuple) and len(fact) == 3:
                                subject, relation, obj = fact
                                kg.add_fact(subject, relation, obj)
                            else:
                                print(f"Skipping invalid fact in {filename}: {line}")
                        except Exception as e:
                            print(f"Error parsing line in {filename}: {line}\nError: {e}")
            except Exception as file_error:
                print(f"Could not read file {filename}: {file_error}")

def process_query_json(query_json_str, kg):
    """
    Process a JSON-formatted query.
    
    Expected JSON format for a forward query (subject-based):
      {
          "queryType": "retrieve_fact",
          "subject": "Hypertension",
          "relation": "treated_by"
      }
      
    Or for a reverse query (object-based):
      {
          "queryType": "retrieve_fact_reverse",
          "object": "ACE Inhibitor",
          "relation": "treated_by"
      }
      
    Returns a JSON string with the result.
    """
    try:
        query = json.loads(query_json_str)
    except json.JSONDecodeError as e:
        return json.dumps({"error": "Invalid JSON input.", "details": str(e)})

    query_type = query.get("queryType")
    if query_type == "retrieve_fact":
        subject = query.get("subject")
        relation = query.get("relation")
        if not subject or not relation:
            return json.dumps({"error": "For a forward query, 'subject' and 'relation' are required."})
        results = kg.query_fact(subject, relation)
        return json.dumps({"response": results})
    elif query_type == "retrieve_fact_reverse":
        obj = query.get("object")
        relation = query.get("relation")
        if not obj or not relation:
            return json.dumps({"error": "For a reverse query, 'object' and 'relation' are required."})
        results = kg.query_fact_reverse(obj, relation)
        return json.dumps({"response": results})
    else:
        return json.dumps({"error": "Unsupported queryType provided."})

def main():
    # Set up command-line argument parsing.
    parser = argparse.ArgumentParser(description="Knowledge Graph Query System")
    group = parser.add_mutually_exclusive_group()
    # For forward query (subject-based)
    group.add_argument("-subject", help="The subject for the query (forward query).")
    # For reverse query (object-based)
    group.add_argument("-object", help="The object for the query (reverse query).")
    parser.add_argument("-relation", help="The relation for the query.", required=False)
    args = parser.parse_args()

    # Determine the path to the SKUs folder (assumed to be in the same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sku_folder = os.path.join(script_dir, "SKUs")

    # Instantiate the knowledge graph and load SKUs.
    kg = KnowledgeGraph()
    load_sku_files(sku_folder, kg)

    # For debugging/logging, display all loaded facts.
    print("Loaded Knowledge Graph Facts:")
    for fact in kg.display_facts():
        print(f" - {fact}")

    # Check if a query was provided via command-line arguments.
    if (args.subject or args.object) and args.relation:
        # If -subject is provided, perform forward query.
        if args.subject:
            query_result = kg.query_fact(args.subject, args.relation)
            output_json = json.dumps({
                "queryType": "retrieve_fact",
                "subject": args.subject,
                "relation": args.relation,
                "response": query_result
            })
            print(output_json)
            return
        # If -object is provided, perform reverse query.
        if args.object:
            query_result = kg.query_fact_reverse(args.object, args.relation)
            output_json = json.dumps({
                "queryType": "retrieve_fact_reverse",
                "object": args.object,
                "relation": args.relation,
                "response": query_result
            })
            print(output_json)
            return

    # If no command-line query provided, then run an interactive loop.
    print("\nReady to process JSON queries. Enter a JSON-formatted query, or type 'quit' to exit.")
    while True:
        user_input = input("Enter your JSON query: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        response = process_query_json(user_input, kg)
        print("Output:", response)

if __name__ == "__main__":
    main()
