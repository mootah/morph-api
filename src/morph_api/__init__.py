from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union, Optional
import spacy
import uvicorn

HOST = "127.0.0.1"
PORT = 19634
SERVER_VER = 1
YOMITAN_VER = "25.12.16.0"

app = FastAPI()

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if the model is not found (though it should be installed)
    from spacy.cli.download import download as spacy_download
    spacy_download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class TokenizeRequest(BaseModel):
    text: Union[str, List[str]]
    scanLength: int

class TokenReading(BaseModel):
    text: str
    reading: str

class ScanResult(BaseModel):
    id: str = "scan"
    source: str = "scanning-parser"
    dictionary: Optional[str] = None
    index: int
    content: List[List[TokenReading]]

@app.post("/serverVersion")
async def server_version():
    return {"version": SERVER_VER}

@app.post("/yomitanVersion")
async def yomitan_version():
    return {"version": YOMITAN_VER}

def tokenize_single_text(text: str, index: int) -> ScanResult:
    doc = nlp(text)
    content = []
    for token in doc:
        if token.is_space:
            continue
        # Use token.text to maintain original inflection
        content.append([TokenReading(text=token.text, reading="")])

    return ScanResult(
        index=index,
        content=content
    )

@app.post("/tokenize")
async def tokenize(request: TokenizeRequest) -> List[ScanResult]:
    if isinstance(request.text, str):
        return [tokenize_single_text(request.text, 0)]
    else:
        return [tokenize_single_text(t, i) for i, t in enumerate(request.text)]

def main():
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()
