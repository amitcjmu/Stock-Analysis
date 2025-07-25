import csv
import operator
import xml.etree.ElementTree as ET
from collections import defaultdict


def analyze_dependencies(svg_file, output_csv_file):
    """
    Analyzes a pydeps-generated SVG file to calculate dependency counts.

    Args:
        svg_file (str): Path to the input SVG file.
        output_csv_file (str): Path to the output CSV file.
    """
    try:
        tree = ET.parse(svg_file)
        root = tree.getroot()
    except (FileNotFoundError, ET.ParseError) as e:
        print(f"Error reading or parsing SVG file: {e}")
        return

    # Namespace is often present in SVG files from graphviz
    namespace = '{http://www.w3.org/2000/svg}'

    # Find all edges
    edges = []
    for g in root.findall(f'.//{namespace}g[@class="edge"]'):
        title_element = g.find(f'{namespace}title')
        if title_element is not None and title_element.text:
            edges.append(title_element.text)

    if not edges:
        print("No dependencies found in the SVG file.")
        return

    out_degree = defaultdict(int)
    in_degree = defaultdict(int)
    nodes = set()

    for edge in edges:
        try:
            source, dest = edge.split('->')
            source = source.strip().replace('_', '.') # pydeps replaces . with _
            dest = dest.strip().replace('_', '.')

            nodes.add(source)
            nodes.add(dest)

            out_degree[source] += 1
            in_degree[dest] += 1
        except ValueError:
            # Skip any titles that don't match the "source->dest" format
            continue

    report_data = []
    for node in sorted(list(nodes)):
        incoming = in_degree.get(node, 0)
        outgoing = out_degree.get(node, 0)
        total = incoming + outgoing
        report_data.append({
            'module': node,
            'incoming': incoming,
            'outgoing': outgoing,
            'total': total
        })

    # Sort by total connections, then by module name
    report_data.sort(key=operator.itemgetter('total', 'module'), reverse=True)

    # Write to CSV
    try:
        with open(output_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['module', 'incoming', 'outgoing', 'total'])
            writer.writeheader()
            writer.writerows(report_data)
        print(f"Successfully generated dependency report: {output_csv_file}")
    except IOError:
        print(f"Error: Could not write to file {output_csv_file}")

if __name__ == "__main__":
    analyze_dependencies('dependency_graph.svg', 'dependency_report.csv')
