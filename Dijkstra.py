import random
import torch 

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

def MinDistanceNode(distances: dict, seachSpace: list, rand=False):
    if(len(distances.keys()) == 0): return None

    nodes = {}
    result = float('inf') if min else 0
    for id in seachSpace:
        dist = distances[id]

        if(dist in nodes.keys()):
            nodes[dist].append(id)
        else:
            nodes[dist] = [id]

        if(dist < result):
            result = dist
    
    index = random.randrange(0, len(nodes[result])) if rand else 0
    return nodes[result][index]

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
        current = MinDistanceNode(distances, list(searchSpace))
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

