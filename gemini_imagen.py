import requests

def generate_image_llm(prompt):
    """
    Generate an image using a Colab/ngrok backend given a text prompt.
    Returns a dict with either 'image_url', 'image_base64', or 'error'.
    """
    colab_url = "https://16d4-34-16-217-239.ngrok-free.app/generate_image"  # Use your actual ngrok URL
    try:
        response = requests.post(colab_url, json={"prompt": prompt}, timeout=120)
        if response.status_code == 200:
            data = response.json()
            if "image_base64" in data:
                return {"image_base64": data["image_base64"]}
            elif "image_url" in data:
                return {"image_url": data["image_url"]}
            else:
                return {"error": "No image returned from Colab backend."}
        else:
            return {"error": f"Colab backend error: {response.status_code} {response.text}"}
    except Exception as e:
        return {"error": str(e)}