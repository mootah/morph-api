
# Morph API for asbplayer annotation

This project provides a similar API to [yomitan-api](yomidevs/yomitan-api) for the annotation functionality of [asbplayer](killergerbah/asbplayer), based on [spaCy](explosion/spaCy)'s tokenizer.

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

### `/tokenize`

#### Request

- method: `POST`
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

