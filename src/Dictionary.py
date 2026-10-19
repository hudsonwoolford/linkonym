from nltk.corpus import wordnet
import nltk

#initialise dictionary and download wordnet if not exist
try:
    wordnet.synsets('bark')
except:
    nltk.download('wordnet')
    wordnet.synsets('bark')

def getRecords(word):
    resp = ""
    syn = wordnet.synsets(word)
    if not syn:
        return None

    dform = {
        "n": "noun",
        "v": "verb",
        "a": "adjective",
        "r": "adverb",
        "s": "adjective satellite",
    }
    ctr1 = 1
    ctr2 = 97
    antonyms = list()
    for i in syn[:10]:
        ctr2 = 97
        definition, examples, form = i.definition(), i.examples(), i.pos()
        resp = resp + str(ctr1) + "." + "\n"
        resp = resp + dform[form] + "-" + word + "\n"
        resp = resp + "Definition : " + definition.capitalize() + "." + "\n"
        ctr1 += 1
        if len(examples) > 0:
            resp = resp + "Usage : " + "\n"
            for j in examples:
                resp = resp + chr(ctr2) + ". " + j.capitalize() + "." + "\n"
                ctr2 += 1
        for j in i.lemmas():
            try:
                antonyms.append(j.antonyms()[0].name())
            except IndexError:
                pass
    if len(antonyms) > 0:
        resp = resp + "Antonyms : " + "\n"
        for i in antonyms:
            resp = resp + i + "\n"
    return resp

def formatDictionary(resp):
    lines = resp.strip().split("\n")
    result = {}
    for i in range(1, len(lines) + 1):
        parts = lines[i - 1].split(" ", 2)
        pos_key = f"pos_{i}"
        definition_key = f"definition_{i}"
        result[pos_key] = parts[1].split("-")[0].strip()  # Extracting the part of speech (noun, verb, etc.)
        result[definition_key] = parts[2].split(":")[1].strip()  # Extracting the definition
    return result

def getRecordsAdvanced(word):
    resp = ""
    syn = wordnet.synsets(word)
    if not syn:
        return None
    
    dform = {
        "n": "noun",
        "v": "verb",
        "a": "adjective",
        "r": "adverb",
        "s": "adjective satellite",
    }
    
    ctr1 = 1
    antonyms = set()  # Use a set to avoid duplicates
    result = {}

    for i in syn[:10]:
        pos = i.pos()
        definition, examples, form = i.definition(), i.examples(), pos
        pos_key = f"pos_{ctr1}"
        definition_key = f"definition_{ctr1}"

        # Add the part of speech (noun, verb, etc.)
        result[pos_key] = dform.get(form, form)

        # Add the definition
        result[definition_key] = definition.capitalize()

        ctr1 += 1
        ctr2 = 97
        if examples:
            result[f"usage_{ctr1-1}"] = []
            for j in examples:
                result[f"usage_{ctr1-1}"].append(chr(ctr2) + ". " + j.capitalize() + ".")
                ctr2 += 1

        # Add antonyms
        for j in i.lemmas():
            try:
                antonyms.add(j.antonyms()[0].name())
            except IndexError:
                pass
    
    
    # Add antonyms to the result if found
    if antonyms:
        result["antonyms"] = list(antonyms)
    
    return result