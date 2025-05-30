"""
Social Media Agents module for the Kartr application.
Provides functionality for automating social media management using AI agents.
"""
import os
import json
import uuid
from datetime import datetime, timedelta

# Path to store social media agent data
AGENTS_DIR = os.path.join(os.getcwd(), 'data/agents')
SUBSCRIPTIONS_FILE = os.path.join(AGENTS_DIR, 'subscriptions.json')

# Create directory if it doesn't exist
os.makedirs(AGENTS_DIR, exist_ok=True)

# Sample agent profiles (in production, these would come from a database)
AGENT_PROFILES = [
    {
        "id": "agent_001",
        "name": "ContentPro",
        "specialty": "Content Creation & Scheduling",
        "features": ["AI-driven content generation", "Automated posting", "Content calendar"],
        "monthly_rate": 299,
        "description": "ContentPro creates and schedules engaging posts across all your social platforms using advanced AI.",
        "supported_platforms": ["Instagram", "Twitter", "Facebook", "LinkedIn"]
    },
    {
        "id": "agent_002",
        "name": "EngageBot",
        "specialty": "Audience Engagement",
        "features": ["24/7 comment responses", "DM management", "Sentiment analysis"],
        "monthly_rate": 199,
        "description": "EngageBot handles all audience interactions, responding to comments and messages around the clock.",
        "supported_platforms": ["Instagram", "Twitter", "Facebook", "TikTok"]
    },
    {
        "id": "agent_003",
        "name": "TrendWatcher",
        "specialty": "Trend Analysis & Optimization",
        "features": ["Real-time trend detection", "Hashtag optimization", "Performance analytics"],
        "monthly_rate": 249,
        "description": "TrendWatcher keeps your content relevant by analyzing trends and suggesting optimizations.",
        "supported_platforms": ["Instagram", "Twitter", "TikTok"]
    },
    {
        "id": "agent_004",
        "name": "CommunityBuilder",
        "specialty": "Community Growth & Management",
        "features": ["Follower growth strategies", "Community management", "Influencer outreach"],
        "monthly_rate": 349,
        "description": "CommunityBuilder focuses on growing your audience and nurturing your online community.",
        "supported_platforms": ["Instagram", "Twitter", "Facebook", "Discord"]
    },
    {
        "id": "agent_005",
        "name": "CrisisManager",
        "specialty": "Brand Protection & Crisis Management",
        "features": ["Reputation monitoring", "Crisis detection", "Response planning"],
        "monthly_rate": 399,
        "description": "CrisisManager protects your brand reputation and helps navigate social media crises.",
        "supported_platforms": ["All major platforms"]
    }
]

def get_available_agents():
    """
    Get a list of all available social media agents.
    
    Returns:
        list: List of agent profile dictionaries.
    """
    return AGENT_PROFILES

def get_agent_by_id(agent_id):
    """
    Get an agent profile by ID.
    
    Args:
        agent_id (str): The ID of the agent.
        
    Returns:
        dict: Agent profile or None if not found.
    """
    for profile in AGENT_PROFILES:
        if profile["id"] == agent_id:
            return profile
    return None

def subscribe_to_agent(user_id, agent_id, plan_duration, social_platforms, account_details):
    """
    Subscribe to a social media agent service.
    
    Args:
        user_id (int): ID of the user subscribing.
        agent_id (str): ID of the agent.
        plan_duration (int): Duration in months.
        social_platforms (list): List of social platforms to manage.
        account_details (dict): Details about the user's social accounts.
        
    Returns:
        dict: Subscription information.
    """
    agent = get_agent_by_id(agent_id)
    if not agent:
        return {"error": "Agent not found"}
    
    try:
        # Calculate subscription details
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * plan_duration)
        total_cost = agent["monthly_rate"] * plan_duration
        
        # Create subscription record
        subscription = {
            "subscription_id": str(uuid.uuid4()),
            "user_id": user_id,
            "agent_id": agent_id,
            "agent_name": agent["name"],
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "duration_months": plan_duration,
            "total_cost": total_cost,
            "social_platforms": social_platforms,
            "account_details": account_details,
            "status": "active",
            "date_created": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save to subscriptions file
        save_subscription(subscription)
        
        return {
            "status": "success",
            "subscription_id": subscription["subscription_id"],
            "agent_name": agent["name"],
            "start_date": subscription["start_date"],
            "end_date": subscription["end_date"],
            "total_cost": total_cost
        }
    except Exception as e:
        return {"error": f"Error processing subscription: {str(e)}"}

def save_subscription(subscription):
    """
    Save a subscription record to the subscriptions file.
    
    Args:
        subscription (dict): Subscription information to save.
    """
    subscriptions = []
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                subscriptions = json.load(f)
        except:
            subscriptions = []
    
    subscriptions.append(subscription)
    
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subscriptions, f, indent=2)

def get_user_subscriptions(user_id):
    """
    Get all subscriptions for a specific user.
    
    Args:
        user_id (int): ID of the user.
        
    Returns:
        list: List of subscription records for the user.
    """
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        return []
    
    try:
        with open(SUBSCRIPTIONS_FILE, 'r') as f:
            subscriptions = json.load(f)
        
        # Filter subscriptions for this user
        user_subscriptions = [s for s in subscriptions if s["user_id"] == user_id]
        return user_subscriptions
    except Exception as e:
        print(f"Error getting user subscriptions: {str(e)}")
        return []

def generate_performance_report(subscription_id):
    """
    Generate a performance report for a social media agent subscription.
    
    Args:
        subscription_id (str): ID of the subscription.
        
    Returns:
        dict: Dictionary with performance metrics.
    """
    # In a real implementation, this would fetch actual performance data
    # from the social media platforms and agent activity
    
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        return {"error": "No subscription records found"}
    
    try:
        with open(SUBSCRIPTIONS_FILE, 'r') as f:
            subscriptions = json.load(f)
        
        # Find the specific subscription
        subscription = next((s for s in subscriptions if s["subscription_id"] == subscription_id), None)
        if not subscription:
            return {"error": "Subscription not found"}
        
        # Calculate time passed since subscription started
        start_date = datetime.strptime(subscription["start_date"], '%Y-%m-%d')
        days_active = (datetime.now() - start_date).days
        if days_active < 0:
            days_active = 0
        
        # Get the agent details
        agent = get_agent_by_id(subscription["agent_id"])
        if not agent:
            return {"error": "Agent not found"}
        
        # Generate sample metrics based on agent type and time active
        metrics = {
            "subscription_id": subscription_id,
            "agent_name": agent["name"],
            "days_active": days_active,
            "platforms_managed": subscription["social_platforms"],
            "content_created": int(days_active * 2.5),
            "engagements_handled": int(days_active * 25),
            "audience_growth": f"{int(days_active * 0.5)}%",
            "sentiment_score": round(min(4.5, 3.5 + (days_active * 0.01)), 1),
            "roi_estimate": f"{round(100 + (days_active * 0.2), 1)}%"
        }
        
        # Add agent-specific metrics
        if agent["specialty"] == "Content Creation & Scheduling":
            metrics["post_engagement_rate"] = f"{round(3.2 + (days_active * 0.02), 1)}%"
            metrics["optimal_posting_times"] = ["10:30 AM", "5:45 PM", "8:15 PM"]
        elif agent["specialty"] == "Audience Engagement":
            metrics["response_time"] = f"{round(12 - min(10, days_active * 0.1), 1)} minutes"
            metrics["positive_sentiment_ratio"] = f"{min(92, 75 + days_active * 0.2)}%"
        
        return metrics
    except Exception as e:
        return {"error": f"Error generating performance report: {str(e)}"}