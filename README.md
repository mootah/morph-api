
# Morph API for asbplayer annotation

This project provides a similar API to [yomitan-api](https://github.com/yomidevs/yomitan-api) for the annotation functionality of [asbplayer](https://github.com/killergerbah/asbplayer), based on [spaCy](https://github.com/explosion/spaCy)'s tokenizer.

## Installation

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone this repository:
   ```bash
   git clone https://github.com/mootah/morph-api.git
   cd morph-api
   ```
3. Initialize the project:
   ```bash
   uv sync
   ```
4. Start the server:
   ```bash
   uv run task server
   ```
5. In asbplayer, set the `Yomitan API URL` to `http://127.0.0.1:19634`.

## API

### `/serverVersion`

#### Request

- method: `POST`

#### Example

- response (200):

    ```
    {
        "version": 1
    }
    ```

### `/yomitanVersion`

#### Request

- method: `POST`

#### Example

- response (200):

    ```
    {
        "version": "<latest yomitan version>"
    }
    ```

### `/tokenize`

#### Request

- method: `POST`
- Content-Type: `application/json` or `application/octet-stream` (for JSON bytes)
- body:
    - `text`: `string|list[string]`
    - `scanLength`: `int`

#### Example

- request:

    ```
    {
        "text": "This is it.",
        "scanLength": 10
    }
    ```

- response (200):

    ```
    [
        {
            "id": "scan",
            "source": "scanning-parser",
            "dictionary": null,
            "index": 0,
            "content": [
                [
                    {
                        "text": "This",
                        "reading": ""
                    }
                ],
                [
                    {
                        "text": "is",
                        "reading": ""
                    }
                ],
                [
                    {
                        "text": "it",
                        "reading": ""
                    }
                ],
                [
                    {
                        "text": ".",
                        "reading": ""
                    }
                ]
            ]
        }
    ]
    ```

### `/termEntries`

#### Request

- method: `POST`
- Content-Type: `application/json` or `application/octet-stream` (for JSON bytes)
- body:
    - `term`: `string`

#### Example

- request:

    ```
    {
        "term": "running"
    }
    ```

- response (200):

    ```
    {
        "dictionaryEntries": [
            {
                "type": "term",
                "isPrimary": true,
                "textProcessorRuleChainCandidates": [
                    []
                ],
                "inflectionRuleChainCandidates": [],
                "score": 0,
                "frequencyOrder": 0,
                "dictionaryIndex": 0,
                "dictionaryAlias": "spaCy",
                "sourceTermExactMatchCount": 1,
                "matchPrimaryReading": false,
                "maxOriginalTextLength": 7,
                "headwords": [
                    {
                        "index": 0,
                        "term": "running",
                        "reading": "",
                        "sources": [
                            {
                                "originalText": "running",
                                "transformedText": "running",
                                "deinflectedText": "run",
                                "matchType": "exact",
                                "matchSource": "term",
                                "isPrimary": true
                            }
                        ],
                        "tags": [],
                        "wordClasses": [
                            "VERB"
                        ]
                    }
                ],
                "definitions": [],
                "frequencies": [],
                "pronunciations": []
            }
        ],
        "originalTextLength": 7
    }
    ```
