import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
import googleapiclient.discovery
import googleapiclient.errors

# Configure API keys
YOUTUBE_API_KEY = "AIzaSyBquQ8xlVZzENIhsCnF7IxPHfZ2veuDCrw"
GEMINI_API_KEY = "AIzaSyCeC1SMEJtkiLttsCCFUs1qO8OB4GZGtog" #gemini key here

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def extract_video_id(url):
    """
    Extract YouTube video ID from various URL formats
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    
    match = re.match(youtube_regex, url)
    if match:
        return match.group(6)
    
    # Handle youtu.be format
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]
    
    # If it's already just an ID
    if len(url) == 11:
        return url
        
    return None

def get_channel_id_from_name(channel_name):
    """
    Get a YouTube channel ID from a channel name using search
    """
    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        
        # Search for the channel
        search_response = youtube.search().list(
            q=channel_name,
            type="channel",
            part="snippet",
            maxResults=1
        ).execute()
        
        if not search_response.get("items"):
            return None
            
        # Return the channel ID
        return search_response["items"][0]["snippet"]["channelId"]
        
    except Exception as e:
        print(f"Error finding channel ID: {e}")
        return None

def get_channel_videos(channel_id, max_results=10):
    """
    Get recent videos from a YouTube channel
    """
    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        
        # Get channel uploads playlist ID
        channels_response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()
        
        if not channels_response["items"]:
            return []
            
        uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Get videos from uploads playlist
        videos_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=max_results
        ).execute()
        
        videos = []
        for item in videos_response.get("items", []):
            video_id = item["snippet"]["resourceId"]["videoId"]
            videos.append({
                "id": video_id,
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"]
            })
            
        return videos
        
    except Exception as e:
        print(f"Error fetching channel videos: {e}")
        return []

def get_video_details(video_id):
    """
    Get detailed information about a YouTube video
    """
    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        
        # Get video details
        video_response = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        ).execute()
        
        if not video_response["items"]:
            return None
            
        video_data = video_response["items"][0]
        
        # Add this line to extract snippet
        snippet = video_data["snippet"]
        
        # Get channel details
        channel_id = video_data["snippet"]["channelId"]
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings",
            id=channel_id
        ).execute()
        
        channel_data = channel_response["items"][0]
        
        # Get video comments for additional context
        try:
            comments_response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=10,
                order="relevance"
            ).execute()
            
            comments = []
            for item in comments_response.get("items", []):
                comment_text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment_text)
        except:
            comments = []
        
        # --- Add these lines to extract thumbnail_url and published_at ---
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_url = thumbnails.get('high', {}).get('url') or thumbnails.get('default', {}).get('url')
        published_at = snippet.get('publishedAt')

        return {
            "video_id": video_id,
            "video_title": video_data["snippet"]["title"],
            "video_description": video_data["snippet"]["description"],
            "video_tags": video_data["snippet"].get("tags", []),
            "view_count": video_data["statistics"].get("viewCount", "N/A"),
            "like_count": video_data["statistics"].get("likeCount", "N/A"),
            "comment_count": video_data["statistics"].get("commentCount", "N/A"),
            "channel_id": channel_id,
            "channel_name": channel_data["snippet"]["title"],
            "channel_description": channel_data["snippet"]["description"],
            "channel_keywords": channel_data.get("brandingSettings", {}).get("channel", {}).get("keywords", ""),
            "subscriber_count": channel_data["statistics"].get("subscriberCount", "N/A"),
            "top_comments": comments,
            "thumbnail_url": thumbnail_url,         # <-- Added
            "published_at": published_at,           # <-- Fixed to use local variable
        }
        
    except Exception as e:
        print(f"Error fetching video details: {e}")
        return None

def analyze_content_with_gemini(video_data):
    """
    Use Gemini API to analyze video content and identify sponsors and creator information
    """
    if not video_data:
        return {"error": "No video data available for analysis"}
    
    # Create a comprehensive prompt for Gemini
    prompt = f"""
    Analyze this YouTube video information and extract:
    1. The creator's full name (the person or entity who made the video)
    2. The creator's primary industry/niche (be specific)
    3. All sponsors mentioned in the video (companies paying for promotion)
    4. Each sponsor's industry sector
    
    VIDEO INFORMATION:
    Title: {video_data['video_title']}
    
    Description:
    {video_data['video_description']}
    
    Channel: {video_data['channel_name']}
    Channel Description: {video_data['channel_description']}
    Channel Keywords: {video_data['channel_keywords']}
    
    Video Tags: {', '.join(video_data.get('video_tags', []))}
    
    Top Comments:
    {' | '.join(video_data.get('top_comments', [])[:5])}
    
    Format your response as a JSON object with this structure:
    {{
        "creator": {{
            "name": "Full Creator Name",
            "industry": "Specific Industry/Niche"
        }},
        "sponsors": [
            {{
                "name": "Sponsor Company Name",
                "industry": "Sponsor's Industry Sector"
            }}
        ]
    }}
    
    If no sponsors are detected, return an empty array for sponsors.
    Provide only the JSON object, no additional text.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        
        # Clean up any markdown formatting
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        
        # Parse JSON
        analysis_result = json.loads(json_str)
        return analysis_result
        
    except Exception as e:
        print(f"Error analyzing with Gemini: {e}")
        return {"error": f"Failed to analyze content: {str(e)}"}

def analyze_influencer_sponsors(video_url_or_id):
    """
    Main function to analyze a YouTube video for influencer and sponsor information
    """
    # Extract video ID
    video_id = extract_video_id(video_url_or_id)
    if not video_id:
        return {"error": "Invalid YouTube URL or video ID"}
    
    # Get detailed video information
    video_data = get_video_details(video_id)
    if not video_data:
        return {"error": "Failed to retrieve video details"}
    
    # Analyze content with Gemini
    analysis = analyze_content_with_gemini(video_data)
    
    # Combine results
    result = {
        "video_id": video_id,
        "video_title": video_data["video_title"],
        "channel_name": video_data["channel_name"],
        "view_count": video_data["view_count"],
        "subscriber_count": video_data["subscriber_count"],
        "thumbnail_url": video_data.get("thumbnail_url", ""),    # <-- Add this line
        "published_at": video_data.get("published_at", ""),      # <-- Add this line
        "analysis": analysis
    }
    
    return result

def batch_analyze_channel(channel_name_or_id, max_videos=5):
    """
    Analyze multiple recent videos from a channel to identify consistent sponsors
    """
    # First check if input is a channel ID or name
    if channel_name_or_id.startswith("UC") and len(channel_name_or_id) == 24:
        # It's likely a channel ID
        channel_id = channel_name_or_id
    else:
        # Try to get channel ID from name
        channel_id = get_channel_id_from_name(channel_name_or_id)
        if not channel_id:
            return {"error": f"Could not find channel with name: {channel_name_or_id}"}
    
    videos = get_channel_videos(channel_id, max_results=max_videos)
    if not videos:
        return {"error": "Failed to retrieve channel videos"}
    
    results = []
    for video in videos:
        print(f"Analyzing video: {video['title']}")
        analysis = analyze_influencer_sponsors(video["id"])
        results.append(analysis)
    
    # Aggregate sponsor data
    all_sponsors = {}
    for result in results:
        if "analysis" in result and "sponsors" in result["analysis"]:
            for sponsor in result["analysis"]["sponsors"]:
                sponsor_name = sponsor["name"]
                if sponsor_name in all_sponsors:
                    all_sponsors[sponsor_name]["count"] += 1
                else:
                    all_sponsors[sponsor_name] = {
                        "industry": sponsor["industry"],
                        "count": 1
                    }
    
    # Sort sponsors by frequency
    sorted_sponsors = [{"name": name, "industry": data["industry"], "frequency": data["count"]} 
                      for name, data in sorted(all_sponsors.items(), key=lambda x: x[1]["count"], reverse=True)]
    
    return {
        "channel_id": channel_id,
        "videos_analyzed": len(results),
        "creator": results[0]["analysis"]["creator"] if results and "analysis" in results[0] else {},
        "common_sponsors": sorted_sponsors
    }

if __name__ == "__main__":
    print("YouTube Influencer and Sponsor Analyzer")
    print("---------------------------------------")
    
    mode = input("Analyze (1) Single video or (2) Channel? Enter 1 or 2: ")
    
    if mode == "1":
        video_url = input("Enter YouTube video URL or ID: ")
        result = analyze_influencer_sponsors(video_url)
        print("\nAnalysis Result:")
        print(json.dumps(result, indent=2))
        
    elif mode == "2":
        channel_name = input("Enter YouTube channel name or ID: ")
        max_videos = int(input("Number of recent videos to analyze (1-10): "))
        result = batch_analyze_channel(channel_name, max_videos=max(1, min(10, max_videos)))
        print("\nChannel Analysis Result:")
        print(json.dumps(result, indent=2))
        
    else:
        print("Invalid selection. Please run the script again.")

