import os
import base64
import requests
import csv
from datetime import datetime

def enhance_prompt_with_brand(prompt, brand_name):
    if brand_name.lower() not in prompt.lower():
        return f"{prompt} This image is brought to you by {brand_name}."
    return prompt

def create_promotional_image_colab(face_image_path, brand_image_path, prompt, brand_name):
    """
    Sends two images and a prompt to the Colab/ngrok backend for promotional image generation.
    Args:
        face_image_path (str): Path to the face image file.
        brand_image_path (str): Path to the brand image file.
        prompt (str): The prompt describing the image content.
        brand_name (str): The name of the brand to promote.
    Returns:
        dict: The response from Colab, typically containing image_base64 or error.
    """
    colab_url = "https://77cc-34-106-14-24.ngrok-free.app/create_promotional_image"  # Use the full endpoint path
    try:
        with open(face_image_path, "rb") as f:
            face_image_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(brand_image_path, "rb") as f:
            brand_image_b64 = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "face_image_base64": face_image_b64,
            "brand_image_base64": brand_image_b64,
            "prompt": prompt,
            "brand_name": brand_name
        }
        response = requests.post(colab_url, json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            output_image_b64 = data.get("image_base64", "")
            result = {"image_base64": output_image_b64} if output_image_b64 else {"error": data.get("error", "No image returned from Colab backend.")}
        else:
            output_image_b64 = ""
            result = {"error": f"Colab backend error: {response.status_code} {response.text}"}
    except Exception as e:
        output_image_b64 = ""
        result = {"error": str(e)}
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    # Save output image if available (optional, for backup)
    if output_image_b64:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_image_path = os.path.join(data_dir, f"output_{timestamp}.png")
        with open(output_image_path, "wb") as img_file:
            img_file.write(base64.b64decode(output_image_b64))
    # Save to CSV in data folder (store images as base64)
    csv_path = os.path.join(data_dir, "generated_images.csv")
    fieldnames = ["face_image_base64", "brand_image_base64", "brand_name", "prompt", "output_image_base64"]
    row = {
        "face_image_base64": face_image_b64,
        "brand_image_base64": brand_image_b64,
        "brand_name": brand_name,
        "prompt": prompt,
        "output_image_base64": output_image_b64
    }
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return result