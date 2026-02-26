from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, ValidationError
from typing import List, Union, Optional
import spacy
import uvicorn
import json

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

@app.post(
    "/tokenize",
    response_model=List[ScanResult],
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": TokenizeRequest.model_json_schema()
                },
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                    "description": "Raw text or JSON bytes to tokenize"
                }
            }
        }
    }
)
async def tokenize(request: Request) -> List[ScanResult]:
    content_type = request.headers.get("Content-Type", "")
    is_json_ct = "application/json" in content_type

    body = await request.body()
    if not body:
        raise HTTPException(status_code=422, detail="Empty body")

    tokenize_request = None
    try:
        # Try parsing as JSON
        data = json.loads(body)
        if isinstance(data, dict):
            try:
                tokenize_request = TokenizeRequest.model_validate(data)
            except ValidationError as e:
                # If it's application/json, it should be a valid TokenizeRequest
                if is_json_ct:
                    raise HTTPException(status_code=422, detail=str(e))
        elif is_json_ct:
            raise HTTPException(status_code=422, detail="JSON body must be an object")
    except json.JSONDecodeError as e:
        if is_json_ct:
            raise HTTPException(status_code=422, detail=f"Invalid JSON: {str(e)}")

    if tokenize_request is None:
        # Fallback to raw bytes as text
        try:
            text = body.decode("utf-8")
            tokenize_request = TokenizeRequest(text=text, scanLength=len(text))
        except UnicodeDecodeError:
            raise HTTPException(status_code=422, detail="Invalid JSON or UTF-8 content")

    if isinstance(tokenize_request.text, str):
        return [tokenize_single_text(tokenize_request.text, 0)]
    else:
        return [tokenize_single_text(t, i) for i, t in enumerate(tokenize_request.text)]

def main():
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()
