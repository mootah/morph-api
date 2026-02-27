from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, ValidationError
from typing import List, Union, Optional
from functools import lru_cache
import logging
import spacy
import uvicorn
from bs4 import BeautifulSoup
import json
import re

SERVER_VER = 1
YOMITAN_VER = "25.12.16.0"

app = FastAPI()

logger = logging.getLogger("uvicorn.app")

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

class TermEntriesRequest(BaseModel):
    term: str

class TermSource(BaseModel):
    originalText: str
    transformedText: str
    deinflectedText: str
    matchType: str
    matchSource: str
    isPrimary: bool

class Headword(BaseModel):
    index: int
    term: str
    reading: str
    sources: List[TermSource]
    tags: List[dict]
    wordClasses: List[str]

class DictionaryEntry(BaseModel):
    type: str
    isPrimary: bool
    textProcessorRuleChainCandidates: List[List[str]]
    inflectionRuleChainCandidates: List[dict]
    score: int
    frequencyOrder: int
    dictionaryIndex: int
    dictionaryAlias: str
    sourceTermExactMatchCount: int
    matchPrimaryReading: bool
    maxOriginalTextLength: int
    headwords: List[Headword]
    definitions: List[dict]
    frequencies: List[dict]
    pronunciations: List[dict]

class TermEntriesResponse(BaseModel):
    dictionaryEntries: List[DictionaryEntry]
    originalTextLength: int

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

def sanitize_text(text):
    # Remove HTML tags
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()
    # Remove cloze deletions
    text = re.sub(r'\{\{c\d+::([^}]+)\}\}', r'\1', text)
    # Keep only ASCII characters
    # text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def tokenize_single_text(text: str, index: int) -> ScanResult:
    text = sanitize_text(text)
    doc = nlp(text)
    content = []
    for token in doc:
        # Use token.text to maintain original inflection
        content.append([TokenReading(text=token.text, reading="")])
        if token.whitespace_:
            content.append([TokenReading(text=" ", reading="")])

    return ScanResult(
        index=index,
        content=content
    )

@lru_cache(maxsize=128)
def _tokenize_internal(body: bytes) -> List[ScanResult]:
    try:
        data = json.loads(body)
        tokenize_request = TokenizeRequest.model_validate(data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if isinstance(tokenize_request.text, str):
        return [tokenize_single_text(tokenize_request.text, 0)]
    else:
        return [tokenize_single_text(t, i) for i, t in enumerate(tokenize_request.text)]

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
                    "description": "JSON bytes to tokenize (must match TokenizeRequest schema)"
                }
            }
        }
    }
)
async def tokenize(request: Request) -> List[ScanResult]:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=422, detail="Empty body")

    return _tokenize_internal(body)

@lru_cache(maxsize=128)
def _term_entries_internal(body: bytes) -> TermEntriesResponse:
    try:
        data = json.loads(body)
        term_request = TermEntriesRequest.model_validate(data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # logger.info(f"term: {repr(term_request.term)}")
    originalText = term_request.term
    doc = nlp(originalText.lower())
    dictionary_entries = []

    for token in doc:
        if token.is_space:
            continue

        source = TermSource(
            originalText=originalText,
            transformedText=token.text,
            deinflectedText=token.lemma_,
            matchType="exact",
            matchSource="term",
            isPrimary=True
        )

        headword = Headword(
            index=0,
            term=token.text,
            reading="",
            sources=[source],
            tags=[],
            wordClasses=[token.pos_]
        )

        entry = DictionaryEntry(
            type="term",
            isPrimary=True,
            textProcessorRuleChainCandidates=[[]],
            inflectionRuleChainCandidates=[],
            score=0,
            frequencyOrder=0,
            dictionaryIndex=0,
            dictionaryAlias="spaCy",
            sourceTermExactMatchCount=1,
            matchPrimaryReading=False,
            maxOriginalTextLength=len(originalText),
            headwords=[headword],
            definitions=[],
            frequencies=[],
            pronunciations=[]
        )
        dictionary_entries.append(entry)

    return TermEntriesResponse(
        dictionaryEntries=dictionary_entries,
        originalTextLength=len(originalText)
    )

@app.post(
    "/termEntries",
    response_model=TermEntriesResponse,
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": TermEntriesRequest.model_json_schema()
                },
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                    "description": "JSON bytes of the term (must match TermEntriesRequest schema)"
                }
            }
        }
    }
)
async def term_entries(request: Request) -> TermEntriesResponse:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=422, detail="Empty body")

    return _term_entries_internal(body)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=19634, log_level="debug")

