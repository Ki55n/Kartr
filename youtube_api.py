import os
import logging
import re
from urllib.parse import urlparse, parse_qs
import googleapiclient.discovery
import googleapiclient.errors
from stats import API_KEY as YOUTUBE_API_KEY

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get YouTube API key from stats.py
API_KEY = YOUTUBE_API_KEY

def get_youtube_service():
    """Create and return the YouTube API service."""
    if not API_KEY:
        logger.warning("YouTube API key not found in environment variables")
        
    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=API_KEY
        )
        return youtube
    except Exception as e:
        logger.error(f"Error building YouTube service: {str(e)}")
        return None

def extract_video_id(url):
    """Extract the video ID from a YouTube URL."""
    if not url:
        return None
    
    # Parse the URL
    parsed_url = urlparse(url)
    
    # YouTube URLs can be in different formats
    if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed_url.path[1:]
    
    if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        
        if parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
            
        if parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    
    # Try to extract video ID using regex for other formats
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    
    return None

def get_video_stats(youtube_url):
    """Get statistics for a YouTube video."""
    video_id = extract_video_id(youtube_url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {youtube_url}")
        return None
    
    youtube = get_youtube_service()
    if not youtube:
        return None
    
    try:
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        )
        response = request.execute()
        
        if not response.get("items"):
            logger.warning(f"No video found with ID: {video_id}")
            return None
        
        video_data = response["items"][0]
        
        return {
            "video_id": video_id,
            "title": video_data["snippet"]["title"],
            "channel_id": video_data["snippet"]["channelId"],
            "channel_title": video_data["snippet"]["channelTitle"],
            "publish_date": video_data["snippet"]["publishedAt"],
            "description": video_data["snippet"]["description"],
            "view_count": int(video_data["statistics"].get("viewCount", 0)),
            "like_count": int(video_data["statistics"].get("likeCount", 0)),
            "comment_count": int(video_data["statistics"].get("commentCount", 0)),
            "duration": video_data["contentDetails"]["duration"],
            "thumbnail_url": video_data["snippet"]["thumbnails"]["high"]["url"]
        }
    except googleapiclient.errors.HttpError as e:
        logger.error(f"YouTube API HttpError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting video stats: {str(e)}")
        return None

def get_channel_stats(channel_id):
    """Get statistics for a YouTube channel."""
    if not channel_id:
        return None
    
    youtube = get_youtube_service()
    if not youtube:
        return None
    
    try:
        request = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            id=channel_id
        )
        response = request.execute()
        
        if not response.get("items"):
            logger.warning(f"No channel found with ID: {channel_id}")
            return None
        
        channel_data = response["items"][0]
        
        return {
            "channel_id": channel_id,
            "title": channel_data["snippet"]["title"],
            "description": channel_data["snippet"]["description"],
            "subscriber_count": int(channel_data["statistics"].get("subscriberCount", 0)),
            "video_count": int(channel_data["statistics"].get("videoCount", 0)),
            "view_count": int(channel_data["statistics"].get("viewCount", 0)),
            "country": channel_data["snippet"].get("country", "Unknown"),
            "thumbnail_url": channel_data["snippet"]["thumbnails"]["high"]["url"],
            "created_at": channel_data["snippet"]["publishedAt"]
        }
    except googleapiclient.errors.HttpError as e:
        logger.error(f"YouTube API HttpError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting channel stats: {str(e)}")
        return None

def extract_video_info(youtube_url):
    """Extract information from a YouTube video useful for sponsors or influencers."""
    video_id = extract_video_id(youtube_url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {youtube_url}")
        return None
    
    youtube = get_youtube_service()
    if not youtube:
        return None
    
    try:
        # Get video details
        video_data = get_video_stats(youtube_url)
        if not video_data:
            return None
        
        # Get channel details
        channel_data = get_channel_stats(video_data["channel_id"])
        if not channel_data:
            return None
        
        # Get video comments
        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100
            )
            response = request.execute()
            comments = response.get("items", [])
        except Exception as e:
            logger.warning(f"Error fetching video comments: {str(e)}")
            comments = []
        
        # Analyze video content and comments for insights
        keywords = extract_keywords(video_data["description"])
        comment_sentiment = analyze_comments(comments)
        
        # Prepare the result
        video_info = {
            "video_id": video_id,
            "title": video_data["title"],
            "channel_id": video_data["channel_id"],
            "channel_title": video_data["channel_title"],
            "subscriber_count": channel_data["subscriber_count"],
            "view_count": video_data["view_count"],
            "like_count": video_data["like_count"],
            "comment_count": video_data["comment_count"],
            "engagement_rate": calculate_engagement_rate(video_data, channel_data),
            "keywords": keywords,
            "comment_sentiment": comment_sentiment,
            "top_comments": extract_top_comments(comments),
            "potential_sponsors": identify_potential_sponsors(comments, video_data["description"]),
            "influencer_info": {
                "name": channel_data["title"],
                "subscribers": channel_data["subscriber_count"],
                "total_videos": channel_data["video_count"],
                "total_views": channel_data["view_count"]
            }
        }
        
        return video_info
    except Exception as e:
        logger.error(f"Error extracting video info: {str(e)}")
        return None

def calculate_engagement_rate(video_data, channel_data):
    """Calculate engagement rate for a video."""
    try:
        engagement = video_data["like_count"] + video_data["comment_count"]
        if video_data["view_count"] == 0:
            return 0
        
        return round((engagement / video_data["view_count"]) * 100, 2)
    except Exception as e:
        logger.error(f"Error calculating engagement rate: {str(e)}")
        return 0

def extract_keywords(text):
    """Extract keywords from text using simple frequency analysis."""
    if not text:
        return []
    
    # Remove common words and special characters
    common_words = {
        "a", "the", "and", "in", "to", "of", "it", "is", "that", "this", 
        "for", "you", "on", "with", "are", "be", "as", "by", "an", "i", 
        "was", "at", "have", "my", "your", "from", "we", "they", "them",
        "their", "his", "her", "he", "she"
    }
    
    # Clean the text and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Count word frequency excluding common words
    word_counts = {}
    for word in words:
        if word not in common_words and len(word) > 3:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency and take top 10
    top_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return [keyword for keyword, count in top_keywords]

def analyze_comments(comments):
    """Simple sentiment analysis on comments."""
    if not comments:
        return {
            "positive": 0,
            "neutral": 0,
            "negative": 0
        }
    
    positive_words = {"great", "good", "amazing", "awesome", "excellent", "love", "best", "perfect"}
    negative_words = {"bad", "terrible", "awful", "worst", "hate", "disappointing", "poor", "horrible"}
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for comment in comments:
        text = comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"].lower()
        
        has_positive = any(word in text for word in positive_words)
        has_negative = any(word in text for word in negative_words)
        
        if has_positive and not has_negative:
            positive_count += 1
        elif has_negative and not has_positive:
            negative_count += 1
        else:
            neutral_count += 1
    
    total = len(comments)
    if total == 0:
        return {
            "positive": 0,
            "neutral": 0,
            "negative": 0
        }
    
    return {
        "positive": round((positive_count / total) * 100, 2),
        "neutral": round((neutral_count / total) * 100, 2),
        "negative": round((negative_count / total) * 100, 2)
    }

def extract_top_comments(comments, limit=5):
    """Extract top comments based on like count."""
    if not comments:
        return []
    
    sorted_comments = sorted(
        comments, 
        key=lambda x: x["snippet"]["topLevelComment"]["snippet"].get("likeCount", 0), 
        reverse=True
    )
    
    top_comments = []
    for comment in sorted_comments[:limit]:
        comment_data = comment["snippet"]["topLevelComment"]["snippet"]
        top_comments.append({
            "author": comment_data.get("authorDisplayName", "Anonymous"),
            "text": comment_data.get("textDisplay", ""),
            "likes": comment_data.get("likeCount", 0),
            "published_at": comment_data.get("publishedAt", "")
        })
    
    return top_comments

def identify_potential_sponsors(comments, description):
    """Identify potential sponsors from video description and comments."""
    # List of common sponsor indicators
    sponsor_indicators = [
        "sponsored by", "thanks to", "brought to you by", "special thanks to",
        "partner with", "sponsored video", "ad", "affiliate", "promotional",
        "discount code", "promo code", "coupon", "use code", "check out"
    ]
    
    potential_sponsors = set()
    
    # Check the description for sponsor mentions
    description_lower = description.lower()
    for indicator in sponsor_indicators:
        if indicator in description_lower:
            # Find the potential sponsor name
            index = description_lower.find(indicator) + len(indicator)
            if index < len(description):
                # Extract a chunk of text after the indicator
                potential_text = description[index:index + 50].strip()
                # Extract the first word or phrase that might be a brand name
                match = re.search(r'[A-Z][a-zA-Z0-9]*(?:\s[A-Z][a-zA-Z0-9]*)*', potential_text)
                if match:
                    potential_sponsors.add(match.group(0))
    
    # Check comments for sponsor mentions
    for comment in comments:
        text = comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        text_lower = text.lower()
        
        for indicator in sponsor_indicators:
            if indicator in text_lower:
                # Find the potential sponsor name similar to above
                index = text_lower.find(indicator) + len(indicator)
                if index < len(text):
                    potential_text = text[index:index + 50].strip()
                    match = re.search(r'[A-Z][a-zA-Z0-9]*(?:\s[A-Z][a-zA-Z0-9]*)*', potential_text)
                    if match:
                        potential_sponsors.add(match.group(0))
    
    return list(potential_sponsors)
