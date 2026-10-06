import config
import requests
import json
import mimetypes

FB_API_BASE = "https://graph.facebook.com/v19.0"

def test_feed_post():
    image_path = "test_image_1.jpg"
    
    # Step 1: Upload photo as unpublished
    print("Uploading photo...")
    url_photos = f"{FB_API_BASE}/{config.FB_PAGE_ID}/photos"
    mime_type, _ = mimetypes.guess_type(image_path)
    with open(image_path, "rb") as f:
        files = {"source": (image_path, f, mime_type)}
        params = {
            "access_token": config.FB_PAGE_ACCESS_TOKEN,
            "published": "false",
        }
        resp = requests.post(url_photos, files=files, data=params) # Note: params vs data for requests
        
        if resp.status_code != 200:
            print("Failed step 1:", resp.text)
            return
            
        photo_id = resp.json().get("id")
        print(f"Uploaded! Photo ID: {photo_id}")
        
    # Step 2: Publish to feed
    print("Publishing to feed...")
    url_feed = f"{FB_API_BASE}/{config.FB_PAGE_ID}/feed"
    data = {
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
        "message": "Testing new feed post format for visibility 🚀",
        "attached_media": json.dumps([{"media_fbid": photo_id}])
    }
    resp = requests.post(url_feed, data=data)
    
    if resp.status_code != 200:
        print("Failed step 2:", resp.text)
    else:
        print("Success!", resp.json())

test_feed_post()
