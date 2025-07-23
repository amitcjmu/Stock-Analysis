import argparse
import ast
import logging
import os

import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_imports(filepath):
    """
    Parses a Python file and returns a list of imported modules.
    """
    imports = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except Exception as e:
            logging.error(f"Could not parse {filepath}: {e}")
            return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def build_dependency_graph(root_dir):
    """
    Builds a dependency graph for all Python files in a directory.
    """
    graph = nx.DiGraph()
    root_dir = os.path.abspath(root_dir)
    
    py_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py') and filename != '__init__.py':
                py_files.append(os.path.join(dirpath, filename))

    module_map = {}
    for py_file in py_files:
        # Construct module name from file path
        rel_path = os.path.relpath(py_file, os.path.commonpath(py_files))
        module_name = os.path.splitext(rel_path.replace(os.sep, '.'))[0]
        module_map[py_file] = module_name
        graph.add_node(module_name)

    for py_file, module_name in module_map.items():
        imports = get_imports(py_file)
        for imp in imports:
            # This is a simplification. It doesn't handle relative imports well
            # or map imported names back to the correct full module path.
            # For this codebase, we will focus on top-level imports.
            
            # Find a node in the graph that matches the import
            for node in graph.nodes():
                if node.endswith(f'.{imp}') or node == imp:
                    if node != module_name:
                         graph.add_edge(module_name, node)
                    break
                # Handle cases like `from app.api.v1 import users`
                elif f".{imp}" in node:
                     if node != module_name:
                        graph.add_edge(module_name, node)

    return graph

def draw_graph(graph, output_filename):
    """
    Draws the graph using pygraphviz or falls back to matplotlib.
    """
    try:
        import pygraphviz as pgv
        logging.info("Using pygraphviz to draw the graph.")
        agn = nx.nx_agraph.to_agraph(graph)
        agn.layout(prog='dot')
        agn.draw(output_filename)
        logging.info(f"Graph saved to {output_filename}")
    except ImportError:
        logging.warning("pygraphviz not found. Falling back to matplotlib.")
        logging.warning("Matplotlib layout can be slow for large graphs.")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(graph, k=0.15, iterations=20)
        nx.draw(graph, pos, with_labels=True, node_size=50, font_size=8, arrows=True)
        plt.savefig(output_filename)
        logging.info(f"Graph saved to {output_filename}")
    except Exception as e:
        logging.error(f"An error occurred during graph drawing: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a Python dependency graph.')
    parser.add_argument('--path', default='backend/app', help='The root directory of the Python code to analyze.')
    parser.add_argument('--output', default='dependency_graph.png', help='The output image file name.')
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        logging.error(f"Provided path '{args.path}' is not a valid directory.")
    else:
        logging.info(f"Analyzing Python code in '{args.path}'...")
        dep_graph = build_dependency_graph(args.path)
        logging.info(f"Found {dep_graph.number_of_nodes()} modules and {dep_graph.number_of_edges()} dependencies.")
        draw_graph(dep_graph, args.output) 