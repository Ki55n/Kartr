# Remove Flask app creation from this file and define route functions to be registered elsewhere
import os
import io
from flask import request, jsonify
from atproto import Client, models

# Bluesky credentials (use environment variables for security in production)
HANDLE = 'influencerkartr.bsky.social'
PASSWORD = 'uode-ikgp-nh7p-vo3o'

def post_to_bluesky():
    data = request.get_json()
    filename = data.get('filename')
    caption = data.get('caption', 'Hello World!')
    image_path = os.path.join('data', filename)

    if not os.path.exists(image_path):
        return jsonify({'error': 'Image not found'}), 404

    client = Client()
    client.login(HANDLE, PASSWORD)

    with open(image_path, 'rb') as image_file:
        img_bytes = image_file.read()
    upload = client.upload_blob(img_bytes)

    # Get image dimensions (optional)
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        width, height = img.size
        aspect_ratio = {'width': width, 'height': height}
    except Exception:
        aspect_ratio = None

    images = [models.AppBskyEmbedImages.Image(alt=caption, image=upload.blob, aspectRatio=aspect_ratio)]
    embed = models.AppBskyEmbedImages.Main(images=images)
    post = client.send_post(text=caption, embed=embed)
    return jsonify({'success': True, 'post_uri': post.uri})

# Example usage: send a POST request to /api/post-to-bluesky with JSON body:
# {"filename": "generated_image.png", "caption": "My new post!"}

def list_images():
    data_dir = os.path.join('data')
    if not os.path.exists(data_dir):
        return jsonify({'images': []})
    files = os.listdir(data_dir)
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    images = [f for f in files if os.path.splitext(f)[1].lower() in image_extensions]
    return jsonify({'images': images})