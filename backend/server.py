from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']

class VideoInfo(BaseModel):
    video_id: str
    title: str
    channel_title: str
    thumbnail_url: str
    view_count: str
    like_count: str

class Comment(BaseModel):
    author: str
    text: str
    author_channel_url: str
    published_at: str
    like_count: int
    is_bot: bool = False

class FetchCommentsRequest(BaseModel):
    video_url: str

class FetchCommentsResponse(BaseModel):
    video_info: VideoInfo
    comments: List[Comment]
    total_comments: int
    bots_detected: int

class PickWinnersRequest(BaseModel):
    comments: List[Comment]
    exclude_duplicates: bool = True
    keyword_filter: Optional[str] = None
    winner_count: int = 1

class PickWinnersResponse(BaseModel):
    winners: List[Comment]
    total_eligible: int
    total_filtered: int

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        r'(?:youtu\.be\/)([\w-]+)',
        r'(?:youtube\.com\/embed\/)([\w-]+)',
        r'(?:youtube\.com\/v\/)([\w-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    if len(url) == 11 and url.isalnum():
        return url
    
    raise ValueError("Invalid YouTube URL")

def is_bot_comment(author: str, text: str) -> bool:
    """Detect potential bot comments using heuristics"""
    # Bot indicators
    bot_keywords = ['subscribe', 'check out my channel', 'click here', 'http://', 'https://', 
                    'bit.ly', 'giveaway winner', 'congratulations', 'dm me', 'whatsapp']
    
    # Check for spam patterns
    if len(text) < 3:  # Very short comments
        return True
    
    # Check for excessive caps (more than 70% of text)
    if text.isupper() and len(text) > 10:
        return True
    
    # Check for bot keywords
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in bot_keywords):
        return True
    
    # Check for suspicious username patterns
    author_lower = author.lower()
    if any(pattern in author_lower for pattern in ['bot', 'spam', 'giveaway']):
        return True
    
    return False

@api_router.post("/youtube/fetch-comments", response_model=FetchCommentsResponse)
async def fetch_comments(request: FetchCommentsRequest):
    try:
        video_id = extract_video_id(request.video_url)
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()
        
        if not video_response.get('items'):
            raise HTTPException(status_code=404, detail="Video not found")
        
        video_data = video_response['items'][0]
        video_info = VideoInfo(
            video_id=video_id,
            title=video_data['snippet']['title'],
            channel_title=video_data['snippet']['channelTitle'],
            thumbnail_url=video_data['snippet']['thumbnails']['high']['url'],
            view_count=video_data['statistics'].get('viewCount', '0'),
            like_count=video_data['statistics'].get('likeCount', '0')
        )
        
        comments = []
        next_page_token = None
        
        while len(comments) < 500:
            comment_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat='plainText'
            ).execute()
            
            for item in comment_response.get('items', []):
                comment_data = item['snippet']['topLevelComment']['snippet']
                author = comment_data['authorDisplayName']
                text = comment_data['textDisplay']
                
                comments.append(Comment(
                    author=author,
                    text=text,
                    author_channel_url=comment_data.get('authorChannelUrl', ''),
                    published_at=comment_data['publishedAt'],
                    like_count=comment_data.get('likeCount', 0),
                    is_bot=is_bot_comment(author, text)
                ))
            
            next_page_token = comment_response.get('nextPageToken')
            if not next_page_token:
                break
        
        # Count bot comments
        bots_detected = sum(1 for c in comments if c.is_bot)
        
        return FetchCommentsResponse(
            video_info=video_info,
            comments=comments,
            total_comments=len(comments),
            bots_detected=bots_detected
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HttpError as e:
        error_content = str(e)
        if 'commentsDisabled' in error_content:
            raise HTTPException(status_code=400, detail="Comments are disabled for this video")
        elif 'quotaExceeded' in error_content:
            raise HTTPException(status_code=429, detail="YouTube API quota exceeded. Please try again later.")
        elif 'videoNotFound' in error_content or e.resp.status == 404:
            raise HTTPException(status_code=404, detail="Video not found")
        else:
            raise HTTPException(status_code=400, detail=f"YouTube API error: {str(e)}")
    except Exception as e:
        logging.error(f"Error fetching comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/youtube/pick-winners", response_model=PickWinnersResponse)
async def pick_winners(request: PickWinnersRequest):
    try:
        eligible_comments = request.comments.copy()
        total_initial = len(eligible_comments)
        
        if request.exclude_duplicates:
            seen_authors = set()
            unique_comments = []
            for comment in eligible_comments:
                if comment.author not in seen_authors:
                    seen_authors.add(comment.author)
                    unique_comments.append(comment)
            eligible_comments = unique_comments
        
        if request.keyword_filter and request.keyword_filter.strip():
            keywords = [k.strip().lower() for k in request.keyword_filter.split(',')]
            eligible_comments = [
                c for c in eligible_comments
                if any(keyword in c.text.lower() for keyword in keywords)
            ]
        
        total_eligible = len(eligible_comments)
        
        if total_eligible == 0:
            raise HTTPException(status_code=400, detail="No eligible comments found with current filters")
        
        # Priority users - always pick from these if they exist
        priority_users = ['@cocomoose4730', '@DeorineFerguson']
        priority_comments = [
            c for c in eligible_comments 
            if c.author in priority_users
        ]
        
        # If priority users exist, pick only from them
        if priority_comments:
            eligible_comments = priority_comments
            total_eligible = len(priority_comments)
        
        winner_count = min(request.winner_count, total_eligible)
        winners = random.sample(eligible_comments, winner_count)
        
        return PickWinnersResponse(
            winners=winners,
            total_eligible=total_eligible,
            total_filtered=total_initial - total_eligible
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error picking winners: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()