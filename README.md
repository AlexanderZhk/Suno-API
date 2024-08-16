# Suno-API Fork

This is a fork of the [Suno-API](https://github.com/SunoAI-API/Suno-API) with the same functionality as the original, but with an added `/upload` endpoint that allows you to upload an audio file to Suno.

## New /upload Functionality

The `/upload` endpoint allows you to upload an audio file to Suno. Below is the brief overview of the new endpoint:

### Error Response (usually clip too long / too short)

**Code**: 200

**Response body**:
```json
{
  "status": "error",
  "error": null
}
```

### Success Response

**Code**: 200

**Response body**:
```json
{
  "clip_id": "756c4dc4-f180-4d04-8c44-3a741f7184ba"
}
```

### cURL Example

```sh
curl -X 'POST' \
  'http://127.0.0.1:8000/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@test_T6Jok3.mp3;type=audio/mpeg'
```

### Request URL

```
http://127.0.0.1:8000/upload
```