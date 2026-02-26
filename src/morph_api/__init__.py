from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union, Optional
import spacy
import uvicorn

app = FastAPI()

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if the model is not found (though it should be installed)
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
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
    return {"version": 1}

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
    uvicorn.run(app, host="127.0.0.1", port=19633)

if __name__ == "__main__":
    main()
