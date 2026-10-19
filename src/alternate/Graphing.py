import igraph as ig
import matplotlib.pyplot as plt
import src.FileManager as FileManager
import src.GameLogic as GameLogic

def GraphAdjacencyList(adjList: dict, layout: str = None, edgeWidth: float = 1, edgeColor: str = "#CCCCCC"):
    edges = []
    nodes = adjList.keys()

    for k in nodes:
        for e in adjList[k]:
            edges.append([int(k), int(e)])

    g = ig.Graph(n=len(nodes), edges=edges)
    g.vs['size'] = 10
    # g.vs['size'] = [min(1 + 0.025 * deg, 2.5) for deg in g.degree()]
    g.es['width'] = edgeWidth
    g.es['color'] = edgeColor

    # # Identify and remove isolated nodes (degree == 0)
    # isolated = [v.index for v in g.vs if g.degree(v) == 0]
    # g.delete_vertices(isolated)

    ig.plot(g, bbox=(1920, 1080), target='graph.png', layout=g.layout(layout))

adjList = FileManager.LoadJsonDict('output/SmallAdjacencyList.json')


# verts = 5
# edges = [(0,1), (1, 2), (2,3), (3,4), (0, 4)]
# g = ig.Graph(verts, edges)

# g['title'] = 'Goofy graph'
# g.vs['name'] = ['Llama', 'Alpaca', 'Potato', 'Hudson', 'Flaming chicken']
# g.vs['cool'] = [True, False, False, True, True]
# g.es['kill'] = [True, False, False, True, False]

# fig, ax = plt.subplots(figsize=(5,5))
# ig.plot(
#     g,
#     target=ax,
#     vertex_size=30,
#     vertex_color='salmon',
#     vertex_frame_width=4.0,
#     vertex_frame_color='black',
#     vertex_label=g.vs['name'],
#     vertex_label_size=7.0,
#     edge_width=2,
#     edge_color=['red' if kill else 'blue' for kill in g.es['kill']],
# )
# plt.show()