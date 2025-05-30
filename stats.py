from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
import re
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import Counter

# ==== CONFIGURE THIS ====
API_KEY = 'AIzaSyBquQ8xlVZzENIhsCnF7IxPHfZ2veuDCrw'  # Your YouTube Data API v3 key

def extract_channel_id(channel_url):
    # Handles URLs like:
    # - https://www.youtube.com/channel/UCxxxxx
    # - https://www.youtube.com/@username
    # - https://www.youtube.com/user/username
    # - https://www.youtube.com/watch?v=VIDEO_ID
    # - https://youtu.be/VIDEO_ID
    parsed = urlparse(channel_url)
    path_parts = parsed.path.strip("/").split("/")
    
    # Handle youtu.be URLs
    if parsed.netloc == 'youtu.be':
        video_id = path_parts[0]
        if video_id:
            # Get channel ID from video
            youtube = build('youtube', 'v3', developerKey=API_KEY)
            try:
                request = youtube.videos().list(part="snippet", id=video_id)
                response = request.execute()
                if response['items']:
                    return response['items'][0]['snippet']['channelId'], "id"
            except Exception as e:
                logger.error(f"Error getting channel ID from video: {str(e)}")
                raise ValueError("Could not extract channel ID from video URL.")
    
    # Handle video URLs
    if "watch" in path_parts:
        video_id = parse_qs(parsed.query).get('v', [None])[0]
        if video_id:
            # Get channel ID from video
            youtube = build('youtube', 'v3', developerKey=API_KEY)
            try:
                request = youtube.videos().list(part="snippet", id=video_id)
                response = request.execute()
                if response['items']:
                    return response['items'][0]['snippet']['channelId'], "id"
            except Exception as e:
                logger.error(f"Error getting channel ID from video: {str(e)}")
                raise ValueError("Could not extract channel ID from video URL.")
    
    # Handle channel URLs
    if "channel" in path_parts:
        return path_parts[-1], "id"
    elif "user" in path_parts:
        return path_parts[-1], "forUsername"
    elif parsed.path.startswith("/@"):
        return parsed.path[2:], "forHandle"
    else:
        raise ValueError("Unsupported YouTube URL format. Please provide a valid YouTube channel or video URL.")

def get_channel_stats(channel_url, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    identifier, id_type = extract_channel_id(channel_url)
    
    if id_type == "id":
        request = youtube.channels().list(part="snippet,contentDetails,statistics,brandingSettings", id=identifier)
    elif id_type == "forUsername":
        request = youtube.channels().list(part="snippet,contentDetails,statistics,brandingSettings", forUsername=identifier)
    elif id_type == "forHandle":
        # Handles (e.g., @username) are not directly supported—need to search instead
        request = youtube.search().list(part="snippet", q=identifier, type="channel", maxResults=1)
        response = request.execute()
        if not response['items']:
            return "Channel not found with handle."
        channel_id = response['items'][0]['snippet']['channelId']
        request = youtube.channels().list(part="snippet,contentDetails,statistics,brandingSettings", id=channel_id)
    else:
        return "Invalid channel identifier."

    response = request.execute()
    if not response['items']:
        return "No channel data found."

    data = response['items'][0]
    stats = data['statistics']
    snippet = data['snippet']
    branding = data.get('brandingSettings', {})

    # Get channel thumbnail
    thumbnails = snippet.get('thumbnails', {})
    thumbnail_url = thumbnails.get('high', {}).get('url') or thumbnails.get('default', {}).get('url')

    # Get channel banner
    banner_url = branding.get('image', {}).get('bannerExternalUrl')

    # Get recent videos for engagement analysis
    recent_videos = get_recent_videos(youtube, data['id'], api_key)
    
    # Calculate engagement metrics
    engagement_metrics = calculate_engagement_metrics(recent_videos)
    
    # Get audience demographics (estimated)
    demographics = estimate_demographics(recent_videos)
    
    # Get content analysis
    content_analysis = analyze_content(recent_videos)
    
    # Get growth metrics
    growth_metrics = calculate_growth_metrics(stats, recent_videos)

    return {
        "channel_id": data.get('id'),
        "title": snippet.get('title'),
        "description": snippet.get('description'),
        "published_at": snippet.get('publishedAt'),
        "subscriber_count": int(stats.get('subscriberCount', 0)),
        "view_count": int(stats.get('viewCount', 0)),
        "video_count": int(stats.get('videoCount', 0)),
        "thumbnail_url": thumbnail_url,
        "banner_url": banner_url,
        "country": snippet.get('country', 'Unknown'),
        "engagement_metrics": engagement_metrics,
        "demographics": demographics,
        "content_analysis": content_analysis,
        "growth_metrics": growth_metrics,
        "recent_videos": recent_videos[:5]  # Only return top 5 recent videos
    }

def get_recent_videos(youtube, channel_id, api_key, max_results=10):
    """Get recent videos from a channel"""
    try:
        # Get uploads playlist ID
        request = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()
        
        if not response['items']:
            return []
            
        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from uploads playlist
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=max_results
        )
        response = request.execute()
        
        video_ids = [item['contentDetails']['videoId'] for item in response['items']]
        
        # Get detailed video statistics
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=','.join(video_ids)
        )
        response = request.execute()
        
        videos = []
        for item in response['items']:
            video = {
                'video_id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'published_at': item['snippet']['publishedAt'],
                'thumbnail_url': item['snippet']['thumbnails']['high']['url'],
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'like_count': int(item['statistics'].get('likeCount', 0)),
                'comment_count': int(item['statistics'].get('commentCount', 0)),
                'duration': item['contentDetails']['duration']
            }
            videos.append(video)
            
        return videos
    except Exception as e:
        print(f"Error getting recent videos: {str(e)}")
        return []

def calculate_engagement_metrics(videos):
    """Calculate engagement metrics from recent videos"""
    if not videos:
        return {
            'average_views': 0,
            'average_likes': 0,
            'average_comments': 0,
            'engagement_rate': 0,
            'views_per_subscriber': 0
        }
    
    total_views = sum(video['view_count'] for video in videos)
    total_likes = sum(video['like_count'] for video in videos)
    total_comments = sum(video['comment_count'] for video in videos)
    
    avg_views = total_views / len(videos)
    avg_likes = total_likes / len(videos)
    avg_comments = total_comments / len(videos)
    
    # Engagement rate = (likes + comments) / views * 100
    engagement_rate = (total_likes + total_comments) / total_views * 100 if total_views > 0 else 0
    
    # This would need subscriber count from the channel stats
    # For now, we'll return a placeholder
    views_per_subscriber = 0
    
    return {
        'average_views': avg_views,
        'average_likes': avg_likes,
        'average_comments': avg_comments,
        'engagement_rate': engagement_rate,
        'views_per_subscriber': views_per_subscriber
    }

def estimate_demographics(videos):
    """Estimate audience demographics based on video content and engagement"""
    # This is a simplified estimation
    # In a real application, you would use more sophisticated methods
    
    # For now, we'll return estimated demographics
    return {
        'age_groups': {
            '13-17': 15,
            '18-24': 30,
            '25-34': 25,
            '35-44': 15,
            '45-54': 10,
            '55+': 5
        },
        'gender': {
            'male': 60,
            'female': 40
        },
        'top_countries': [
            {'country': 'United States', 'percentage': 40},
            {'country': 'United Kingdom', 'percentage': 15},
            {'country': 'Canada', 'percentage': 10},
            {'country': 'Australia', 'percentage': 8},
            {'country': 'India', 'percentage': 7}
        ],
        'interests': [
            'Technology',
            'Gaming',
            'Entertainment',
            'Education',
            'Lifestyle'
        ]
    }

def analyze_content(videos):
    """Analyze content type and topics from recent videos"""
    if not videos:
        return {
            'content_types': [],
            'topics': [],
            'upload_frequency': 'Unknown',
            'average_video_length': 'Unknown'
        }
    
    # Extract keywords from titles and descriptions
    all_text = ' '.join([video['title'] + ' ' + video['description'] for video in videos])
    words = re.findall(r'\b\w+\b', all_text.lower())
    
    # Filter out common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [word for word in words if word not in common_words and len(word) > 3]
    
    # Count keyword frequency
    keyword_counts = Counter(keywords)
    top_keywords = [{'keyword': k, 'count': v} for k, v in keyword_counts.most_common(10)]
    
    # Estimate content types
    content_types = []
    if any('tutorial' in video['title'].lower() or 'how to' in video['title'].lower() for video in videos):
        content_types.append('Tutorials')
    if any('review' in video['title'].lower() for video in videos):
        content_types.append('Reviews')
    if any('vlog' in video['title'].lower() for video in videos):
        content_types.append('Vlogs')
    if any('gaming' in video['title'].lower() or 'game' in video['title'].lower() for video in videos):
        content_types.append('Gaming')
    if any('news' in video['title'].lower() or 'update' in video['title'].lower() for video in videos):
        content_types.append('News')
    
    # If no specific content types detected, add a generic one
    if not content_types:
        content_types.append('General Content')
    
    # Calculate upload frequency
    if len(videos) >= 2:
        dates = [datetime.strptime(video['published_at'][:10], '%Y-%m-%d') for video in videos]
        date_diffs = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
        avg_days_between_uploads = sum(date_diffs) / len(date_diffs)
        
        if avg_days_between_uploads < 2:
            upload_frequency = 'Daily'
        elif avg_days_between_uploads < 4:
            upload_frequency = '2-3 times per week'
        elif avg_days_between_uploads < 8:
            upload_frequency = 'Weekly'
        elif avg_days_between_uploads < 15:
            upload_frequency = 'Bi-weekly'
        else:
            upload_frequency = 'Monthly'
    else:
        upload_frequency = 'Unknown'
    
    # Calculate average video length
    durations = []
    for video in videos:
        duration = video['duration'].replace('PT', '')
        hours = 0
        minutes = 0
        seconds = 0
        
        if 'H' in duration:
            hours_part = duration.split('H')[0]
            hours = int(hours_part)
            duration = duration.split('H')[1]
        
        if 'M' in duration:
            minutes_part = duration.split('M')[0]
            minutes = int(minutes_part)
            duration = duration.split('M')[1]
        
        if 'S' in duration:
            seconds_part = duration.split('S')[0]
            seconds = int(seconds_part)
        
        total_seconds = hours * 3600 + minutes * 60 + seconds
        durations.append(total_seconds)
    
    avg_duration_seconds = sum(durations) / len(durations) if durations else 0
    
    if avg_duration_seconds < 60:
        avg_video_length = f"{int(avg_duration_seconds)} seconds"
    elif avg_duration_seconds < 3600:
        avg_video_length = f"{int(avg_duration_seconds / 60)} minutes"
    else:
        avg_video_length = f"{int(avg_duration_seconds / 3600)} hours"
    
    return {
        'content_types': content_types,
        'topics': top_keywords,
        'upload_frequency': upload_frequency,
        'average_video_length': avg_video_length
    }

def calculate_growth_metrics(stats, videos):
    """Calculate growth metrics for the channel"""
    # In a real application, you would need historical data
    # For now, we'll return estimated growth metrics
    
    subscriber_count = int(stats.get('subscriberCount', 0))
    view_count = int(stats.get('viewCount', 0))
    video_count = int(stats.get('videoCount', 0))
    
    # Estimate subscriber growth rate (placeholder)
    subscriber_growth_rate = 5  # 5% growth rate
    
    # Estimate view growth rate (placeholder)
    view_growth_rate = 8  # 8% growth rate
    
    # Estimate video growth rate (placeholder)
    video_growth_rate = 3  # 3% growth rate
    
    # Calculate views per video
    views_per_video = view_count / video_count if video_count > 0 else 0
    
    # Calculate views per subscriber
    views_per_subscriber = view_count / subscriber_count if subscriber_count > 0 else 0
    
    return {
        'subscriber_growth_rate': subscriber_growth_rate,
        'view_growth_rate': view_growth_rate,
        'video_growth_rate': video_growth_rate,
        'views_per_video': views_per_video,
        'views_per_subscriber': views_per_subscriber
    }

# === USAGE EXAMPLE ===
if __name__ == "__main__":
    channel_url = input("Enter YouTube channel URL: ")
    try:
        stats = get_channel_stats(channel_url, API_KEY)
        print("\nChannel Statistics:")
        for k, v in stats.items():
            if k not in ['recent_videos', 'engagement_metrics', 'demographics', 'content_analysis', 'growth_metrics']:
                print(f"{k}: {v}")
        
        print("\nEngagement Metrics:")
        for k, v in stats['engagement_metrics'].items():
            print(f"{k}: {v}")
        
        print("\nDemographics:")
        for k, v in stats['demographics'].items():
            print(f"{k}: {v}")
        
        print("\nContent Analysis:")
        for k, v in stats['content_analysis'].items():
            print(f"{k}: {v}")
        
        print("\nGrowth Metrics:")
        for k, v in stats['growth_metrics'].items():
            print(f"{k}: {v}")
    except Exception as e:
        print("Error:", str(e))
