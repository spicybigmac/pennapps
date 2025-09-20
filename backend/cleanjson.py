import json

def convertJSON(inp):
    cleaned = inp.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.lstrip("```json").lstrip()
    if cleaned.endswith("```"):
        cleaned = cleaned.rstrip("```").rstrip()
    cleaned = cleaned[cleaned.find("{"):] # remove beginning text if gemini outputs stuff 

    output = ""
    curropen = 0
    i = 0
    while i < len(cleaned):
        c = cleaned[i]
        if (c == "\n"):
            curropen = 0
        elif (c == ":"):
            curropen = 2
        elif (c == '"' and not (i == len(cleaned)-1 or cleaned[i+1] == "," or cleaned[i+1] == '\n')):
            if (curropen == 2):
                curropen = 1
            elif (curropen == 1 and i > 0 and cleaned[i-1] != "\\"):
                output += '\\'

        output += c
        i += 1
    print(output)
    output = json.loads(output)
    return output