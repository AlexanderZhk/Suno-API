import json
import os
import time

import aiohttp
from dotenv import load_dotenv
from fastapi import UploadFile, File
import asyncio

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

COMMON_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://suno.com",
    "Origin": "https://suno.com",
}


async def fetch(url, headers=None, data=None, method="POST",raw_response = False):
    if headers is None:
        headers = {}
    headers.update(COMMON_HEADERS)
    if data is not None:
        data = json.dumps(data)

    print(data, method, headers, url)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                method=method, url=url, data=data, headers=headers
            ) as resp:
                if not raw_response:
                    return await resp.json()
                else:
                    print(f"Status: {resp.status}")
                    print(f"Headers: {resp.headers}")
                    print(f"Content: {await resp.text()}")
                    return await resp.text()
        except Exception as e:
            return f"An error occurred: {e}"


async def get_feed(ids, token):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/feed/?ids={ids}"
    response = await fetch(api_url, headers, method="GET")
    return response


async def generate_music(data, token):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/generate/v2/"
    response = await fetch(api_url, headers, data)
    return response


async def generate_lyrics(prompt, token):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/generate/lyrics/"
    data = {"prompt": prompt}
    return await fetch(api_url, headers, data)


async def get_lyrics(lid, token):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/generate/lyrics/{lid}"
    return await fetch(api_url, headers, method="GET")


async def get_credits(token):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/billing/info/"
    respose = await fetch(api_url, headers, method="GET")
    return {
        "credits_left": respose['total_credits_left'],
        "period": respose['period'],
        "monthly_limit": respose['monthly_limit'],
        "monthly_usage": respose['monthly_usage']
    }

async def upload_status(uid, token):
    headers = {"Authorization": f"Bearer {token}"}
    status_url = f"{BASE_URL}/api/uploads/audio/{uid}/"

    elapsed_time = 0
    interval = 3  # Check every 3 seconds
    max_wait_time = 30  # Maximum wait time in seconds

    while elapsed_time < max_wait_time:
        status_response = await fetch(status_url, headers=headers, method="GET")
        if status_response.get("status") == "complete":
            break
        await asyncio.sleep(interval)
        elapsed_time += interval


    return status_response

async def initialize_clip(uid, token):
    headers = {"Authorization": f"Bearer {token}"}
    initialize_url = f"{BASE_URL}/api/uploads/audio/{uid}/initialize-clip/"

    #status_response = await fetch(initialize_url, headers=headers, method="OPTIONS",raw_response=True)
    status_response = await fetch(initialize_url, headers=headers, data={"clip_id": uid}, method="POST")

    print(status_response)

    return status_response

async def upload_audio(file: UploadFile, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"{BASE_URL}/api/uploads/audio/"
    data = {"extension": "mp3"}
    response = await fetch(api_url, headers, data, method="POST")

    if not response.get("is_file_uploaded"):
        s3_url = response["url"]
        fields = response["fields"]

        form_data = aiohttp.FormData()
        form_data.add_field('Content-Type', fields['Content-Type'])
        form_data.add_field('key', fields['key'])
        form_data.add_field('AWSAccessKeyId', fields['AWSAccessKeyId'])
        form_data.add_field('policy', fields['policy'])
        form_data.add_field('signature', fields['signature'])

        filename = ""

        if file:
            file_content = await file.read()
            form_data.add_field('file', file_content, filename=file.filename, content_type='audio/mpeg')
            filename = file.filename
        else:
            with open("./example.mp3", "rb") as f:
                file_content = f.read()
                form_data.add_field('file', file_content, filename='example.mp3', content_type='audio/mpeg')
                filename = "example.mp3"

        async with aiohttp.ClientSession() as session:
            async with session.post(s3_url, data=form_data) as resp:
                if resp.status != 204:
                    return f"Failed to upload file: {resp.status}"

        # Extract the ID from the key
        key = fields['key']
        file_id = key.split('/')[1].split('.')[0]

        # Construct the URL for the upload-finish endpoint
        finish_url = f"https://studio-api.suno.ai/api/uploads/audio/{file_id}/upload-finish/"

        finish_data = {"upload_type": "file_upload", "upload_filename": filename}

        # Make a POST request to the upload-finish endpoint
        finish_response = await fetch(finish_url, headers=headers,data = finish_data, method="POST")

        if finish_response != {}:
            print(finish_response)
            return f"[Finish upload failed] {finish_response}"


        status_response = await upload_status(file_id,token)
        if status_response.get("status") != "complete":
            return {"status":status_response.get("status"),"error":status_response.get("error")}

        print(status_response)


        respose = await initialize_clip(file_id,token)

        return respose



    return "File already uploaded"