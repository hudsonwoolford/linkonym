import random
import WordManager as wm

def GetPath(links: dict, source, target):
    path = [target]
    current = target
    while True:
        current = links[current]
        path.append(current)
        if(current == source):
            break
    
    path.reverse()
    return path

def ClosestNodes(distances: dict, searchSpace: list) -> list:
    if(len(distances.keys()) == 0 or len(searchSpace) == 0): return None

    nodes = {}
    result = float('inf') if min else 0
    for id in searchSpace:
        dist = distances[id]

        if(dist in nodes.keys()):
            nodes[dist].append(id)
        else:
            nodes[dist] = [id]

        if(dist < result):
            result = dist
    
    return nodes[result]

def GreedyNode(distances: dict, searchSpace: list, target: int):
    # closest = ClosestNodes(distances, searchSpace)
    # if(closest == None): return None
    if(len(distances.keys()) == 0 or len(searchSpace) == 0): return None


    bestID = (searchSpace[0], wm.TensorCosSimilarity(wm.IDTensor(searchSpace[0]), wm.IDTensor(target)))
    for id in searchSpace:
        sim = wm.TensorCosSimilarity(wm.IDTensor(id), wm.IDTensor(target))

        if(sim > bestID[1]):
            bestID = (id, sim)

    return bestID[0]

def MinDistanceNode(distances: dict, searchSpace: list, rand=False):
    closest = ClosestNodes(distances, searchSpace)
    if(closest == None): return None

    index = random.randrange(0, len(closest)) if rand else 0
    return closest[index]

def DijkstraPath(adjList: dict, source: int, target: int, banned: list = [], ):
    source = source
    target = target

    #initialise node info (links and distances)
    searchSpace = set({})
    links = {}
    distances = {}
    for node in adjList.keys():
        if(node in banned or node == source):
            continue

        distances[node] = float('inf')
        links[node] = None

    distances[source] = 0
    searchSpace.add(source)
    
    #dijkstra search
    found = False
    while not found:
        current = GreedyNode(distances, list(searchSpace), target)
        if(current == None):
            return None
        
        currentDist = distances.pop(current) #get the min distance node and remove it from dict
        searchSpace.remove(current)

        unvisited = distances.keys()

        # print(distances, current) #tracking
        #iterate through every neighbor of node
        for neighbor in adjList[current]:
            #dont consider already visited nodes
            if(neighbor == current or neighbor not in unvisited):
                continue
            
            if(neighbor not in searchSpace):
                searchSpace.add(neighbor)
            
            #set distance of neighbor 
            newDist = currentDist + 1
            if(newDist < distances[neighbor]):
                distances[neighbor] = currentDist + 1
                links[neighbor] = current

            #completion case
            if(neighbor == target): 
                found = True
                break

    return GetPath(links, source, target) #return shortest path



# allWords = list(shortWordData['vocab'].keys())
# options = []
# for id in wordAL.keys():
#     try:
#         options.append(allWords[int(id)])
#     except:
#         pass

# wordData = torch.load('data/WikipediaWData.pt')
# allWords = list(wordData['vocab'].keys())
# wordAL = torch.load('data/WordAdjacency.pt')
# while True:
#     start = input('Start: ')
#     target = input('Target: ')
#     path = DijkstraPath(wordAL, wordData['vocab'][start]['id'], wordData['vocab'][target]['id'])
#     for id in path:
#         print(id)
         


# Graphing.GraphAdjacencyList(testData6, layout='fr')








# adjList = FileManager.LoadJsonDict('output/AdjacencyList.json')

# allWords = list(GameLogic._WordData['vocab'].keys())

# avgDegree = 0
# isolatedWords = []

# for k in adjList.keys():
#     index = int(k)
#     degree = len(adjList[k])
#     avgDegree += degree
#     if(degree == 0):
#         w = allWords[index]
#         isolatedWords.append(w)

# avgDegree /= len(adjList.keys())

# print(f"Average degree: {avgDegree}")
# print(f"Isolated words: {len(isolatedWords)}")

# if(input('Reveal isolated?: ').lower() == 'y'):
#     print(isolatedWords)

