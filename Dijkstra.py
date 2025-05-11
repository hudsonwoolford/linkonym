import random

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

def MinDistanceNode(distances: dict, rand=False):
    if(len(distances.keys()) == 0): return None

    nodes = {}
    minDist = float('inf')
    for node in distances.keys():
        dist = distances[node]

        if(dist in nodes.keys()):
            nodes[dist].append(node)
        else:
            nodes[dist] = [node]

        if(dist < minDist):
            minDist = dist
    
    index = random.randrange(0, len(nodes[minDist])) if rand else 0
    return nodes[minDist][index]

def DijkstraPath(adjList: dict, source: int, target: int, banned: list = []):
    source = source
    target = target

    #initialise node info (links and distances)
    links = {}
    distances = {}
    for node in adjList.keys():
        if(node in banned):
            continue

        distances[node]= float('inf')
        links[node] = None

    distances[source] = 0
    
    #dijkstra search
    found = False
    while not found:
        current = MinDistanceNode(distances, rand=True) #get the min distance node
        unvisited = distances.keys()
        if(current == None):
            return None

        # print(distances, current) #tracking
        #iterate through every neighbor of node
        for neighbor in adjList[current]:

            #completion case
            if(neighbor == target): 
                found = True
            
            #dont consider already visited nodes
            if(neighbor == current or neighbor not in unvisited):
                continue
            
            #set distance of neighbor 
            distances[neighbor] = distances[current] + 1
            links[neighbor] = current

        #remove visited/analyzed node
        distances.pop(current)
    
    return GetPath(links, source, target) #return shortest path


# wordAL = torch.load('output/NewAdjList.pt')

# allWords = list(shortWordData['vocab'].keys())
# options = []
# for id in wordAL.keys():
#     try:
#         options.append(allWords[int(id)])
#     except:
#         pass

# while True:
#     start = input('Start: ')
#     target = input('Target: ')

#     path = DijkstraPath(wordAL, shortWordData['vocab'][start]['id'], shortWordData['vocab'][target]['id'])
#     print(path)
#     for id in path:
#         print(allWords[id])
         


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

