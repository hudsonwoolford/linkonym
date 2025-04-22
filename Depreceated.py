from warnings import warn

warn("File is for depreceated functions. Dont use this.", DeprecationWarning, stacklevel=2)

def MidpointTensorI(word2embed: dict, word1: str, word2: str, bannedWords: list = None) -> int:
    tensor1 = word2embed[word1]
    tensor2 = word2embed[word2]
    midpoint = (tensor1 + tensor2)/2
    
    allEmbeds = torch.stack(list(word2embed.values()))
    #calculate distances from all embeddings to the midpoint
    distances = torch.norm(allEmbeds - midpoint, dim=1)

    #ban tensor1 and tensor2 by finding their indices and setting those distances to inf
    bannedTensors = [word2embed[bannedWords[i]] for i in range(0, len(bannedWords))]
    bannedTensors.append(tensor1)
    bannedTensors.append(tensor2)
    for t in bannedTensors:
        matches = torch.all(allEmbeds == t, dim=1)
        if matches.any():
            distances[matches] = float('inf')

    closest = torch.argmin(distances)
    return closest

def MidpointWord(lemma2embed: dict, lemma1: str, lemma2: str, bannedWords: list = None) -> str:
    midIndex = int(MidpointTensorI(lemma2embed, lemma1, lemma2, bannedWords=bannedWords))

    return list(lemma2embed.keys())[midIndex]

def ProcessGlove(path: str, minLength: int = 3, maxLength: int = 50, alphabetOnly: bool = False, checkDic: bool = False, allowDigits: bool = True) -> dict:
    f = open(path, "r", encoding="utf-8")
    content = f.read()

    info = {}
    lines = content.split("\n")

    for i, line in enumerate(lines):
        things = line.split(" ")

        word = str(things[0])
        
        barrier = False
        barrier |= len(word) < minLength or len(word) > maxLength
        if(not allowDigits): barrier |= word.isdigit()
        if(barrier): continue

        if(alphabetOnly):
            for c in list(word):
                barrier |= ord(c) < 97 or ord(c)>122
                if(barrier): break
        if(barrier): continue

        if(checkDic):
            wordDic = enchant.Dict("en_US")
            barrier |= not wordDic.check(word)
        if(barrier): continue

        vector = [float(things[i]) for i in range(1, len(things))]
        try:
            info[word] = vector
        except:
            print(f"Weird at line {i}")
            continue

    return info

def ValidatedGuess(possibleValues: list = None, bannedValues: list = None) -> str:
    """
    Returns a guess inputted by user:
        banned ? ask again
        not in values ? change word to lemma
            still not in values ? ask again
    """

    def CheckWordInList(word: str, l: list) -> tuple:
        """
        will check for word in list, if not found: checks for lemma in list
        """

        inList = word in l
        if(not inList):
            word = StanzaUtility.LemmaWord(word, _nlp)
            if(word not in l):
                return False, word
        return True, word
    
    def GetGuess() -> tuple:
        inp = input("Enter a word: ")
        keys, inp = CheckWordInList(inp, possibleValues)
        banned = inp in bannedValues
        return inp, keys, banned

    guess, inKeys, inBanned =  GetGuess()

    while(not inKeys or inBanned):
        if(inBanned):
            print("That word has been banned!")
        if(not inKeys):
            print("I don't know that word :(")

        #guess again
        guess, inKeys, inBanned =  GetGuess()
    
    return guess.strip()

def TextBasedGame():
    won = False
    keys = _WordData["vocab"].keys()
    
    track, target = "",""
    while True:
        track, target = StartEndWords(minDistance=0.5)
        print("Start =", track)
        print("Target =", target)
        
        if(input("Regenerate? (y)") != 'y'):
            break
    
    wordChain = [track]
    bannedWords = []
    while True:
        #get valid guess
        guess = ValidatedGuess(keys, bannedWords)
        while WordSim(track, guess) > DISTANCE_CUTOFF:
            print(f"{track} -> {guess} ({round(WordSim(track, guess), 4)}) is too far")
            guess = ValidatedGuess(keys, bannedWords)

        wordChain.append(guess)
        #check for lemma guess win state
        if(StanzaUtility.LemmaWord(guess, _nlp) == target):
            won = True
            print("Congrats! You won!")
            print("Full word chain:", ' -> '.join(wordChain))
            break

        print(f"Chained: {track} -> {guess} ({round(WordSim(track, guess), 4)})")
        print(f"{guess} is {round(WordSim(guess, target), 4)} away from {target}")
        track = guess
        bannedWords.append(guess)

        #get midpoint of words
        # midword = MidpointWord(lemma2embed, guess, target, bannedWords=bannedWords)
        # bannedWords.append(midword)
        # print(f"{guess} -> {midword}")
    
    if(input("Play again? (y): ").lower() == 'y'):
        TextBasedGame()

def DataToWordList(data: dict, dataRange: range = None):

    if(dataRange==None):
        dataRange = range(data["emb"])

    culledData = StanzaUtility.GetDataRange(data, dataRange=dataRange)

    #get words and embeds
    words = list(culledData['vocab']["_id2unit"].values())
    ids = list(culledData['vocab']["_id2unit"].keys())

    Utility.WordsToJson(words, ids, "WordList.json", minLength=3, maxLength=10)
