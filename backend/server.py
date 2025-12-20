from fastapi import FastAPI, APIRouter, HTTPException, Request
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
import time


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()

# 🔒 Rate limiting settings
RATE_LIMIT = 30            # max requests per IP
RATE_LIMIT_WINDOW = 60    # seconds

# In-memory store for IP request timestamps
ip_requests = {}

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
    author_profile_image_url: str
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
    excluded_authors: List[str] = []  # Previously selected winners to exclude

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
    """Detect bot comments from blacklisted usernames"""
    bot_usernames = {
        '@tylernoahanderson1997', '@Louis-Vincent-Myers', '@Randy.James.Harris',
        '@terrybrown1977', '@austinward23', '@JoshuaEthanCook',
        '@Jeffrey-Jose-Roberts', '@zacharyloganortiz1973', '@subho-v5s',
    }
    
    return author in bot_usernames

def check_rate_limit(request: Request):
    ip = request.client.host
    now = time.time()

    if ip not in ip_requests:
        ip_requests[ip] = []

    ip_requests[ip] = [
        t for t in ip_requests[ip]
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(ip_requests[ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a minute and try again."
        )

    ip_requests[ip].append(now)

@api_router.post("/youtube/fetch-comments", response_model=FetchCommentsResponse)
async def fetch_comments(request: FetchCommentsRequest, req: Request):
    check_rate_limit(req)

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
                    author_profile_image_url=comment_data.get('authorProfileImageUrl', ''),
                    published_at=comment_data['publishedAt'],
                    like_count=comment_data.get('likeCount', 0),
                    is_bot=is_bot_comment(author, text)
                ))
            
            next_page_token = comment_response.get('nextPageToken')
            if not next_page_token:
                break
        
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
async def pick_winners(request: PickWinnersRequest, req: Request):
    check_rate_limit(req)

    # VIP accounts that should always win if present
    VIP_WINNERS = {'@cocomoose4730', '@Vanessa-yt2'}
    
    # Blacklisted users - appear normal in shuffling but can NEVER win
    NEVER_WIN_USERNAMES = {
        '@HarryResearch-s7o', '@hindigyanworld9511', '@jimmyjk007', '@arhambothra3994',
        '@Tamatar-nk1bq', '@Perfect-os8we', '@Warrenxwarren', '@henryjames5757',
        '@SurprisedColourfulShirt-hy1gb', '@Mack0txop0', '@pandagamer6822',
        '@ManageHarryreviews', '@kishan6691', '@Alexander-oq4jj', '@Jethalala-nm4rk',
        '@Gul-vu7gt', '@mrhelmention', '@Benalyhsdhd', '@varsh6871', '@jeffery09090',
        '@goriM-oo4np', '@JefDorris', '@elizamark9990', '@ShortsAmazonaffiliate',
        '@SmoothDrive-w3n', '@CureYourdiabetes', '@Herry-q2p', '@ZackZ-l2k',
        '@DOT-x5k', '@ronakmall8032', '@LondonkaBusiness', '@darksideresearch',
        '@Newzistick', '@CalvinReidStudios', '@zivagamingytvloger328', '@chef_7hb',
        '@Andy933p', '@Vmgaminghddhp2', '@pammipyarelal7997', '@HarryHistory-f6d',
        '@vaanirao999', '@gagandragamerz8473', '@nkgarg8374', '@Keu2nd',
        '@historian2299', '@philipcozzolino8750', '@kristeen961', '@Target100-ns2lq',
        '@dearraj8195', '@loophole9832', '@vinitbhattacharya7299', '@Alwaysfirst007',
        '@sachinkumae9029', '@harryom9357', '@HbBh-yp9eq', '@linusvideoyt',
        '@letsupgrade360', '@punitpareek4520', '@Gold-fo8is', '@rajeshroy2080',
        '@MrDiljeet-n3j', '@gamerrox7337', '@Cody-q7p', '@Prakashxx95',
        '@retropinclub-7793', '@mr.vishnu4804', '@gwblazeyt2295', '@sacinxd',
        '@govindcX0007', '@marquesofficial6838', '@anilsartroom4573', '@jpnewsicstudio4072',
        '@AftoYT', '@hemuandhemu', '@supersaf_2.021', '@vishnugaming8968',
        '@codingclass2794', '@vassimkhanyt3177', '@hunny461', '@anujgamer5739',
        '@neongamer2441', '@workwithGadgetFie', '@ascrafting5644', '@dipakdeepak8193',
        '@utilitygamerz1252', '@kunit3692', '@zaviyar693', '@budgetshop7700',
        '@readhindibook', '@Monk-uo4ib', '@Hunny781', '@Venomguy796',
        '@passionbazz7129', '@udrwatautovlogs2250', '@surajka_gulam133', '@WhatIdid-fe3ji',
        '@mrskrishna7896', '@harryMXmedia', '@EmilyLawsonYT', '@Juan2077m', '@AlanFn-2187',
        '@_rajasthan_royals_r2489', '@lucky750ytc', '@dheeru.07793', '@sridungargarh1937',
        '@MystorageHarish', '@PappuPaldoot', '@GoriShankar-rb8ll', '@Freesmurk',
        '@killersquad6245', '@mayankmalhotra3257', '@NadhaNawshad-h4v', '@reviewgadget5425',
        '@spritalitybyohm184', '@trulytamyra', '@agrowealthfoundation5537', '@AlexGw-w1v',
        '@sumit_yt3838', '@nubier1964', '@BUISNESSACCNT', '@KoolDown345',
        '@Gael40k', '@RickyHeatz', '@robbinthebert', '@Gabrielagho0',
        '@neonzz09', '@UTIE3', '@Rexieluvs', '@totallynotbro',
        '@myajujuju', '@peanutjelly93', '@bljoe89', '@dhruvskirtancorner1557',
        '@totallynotxscarru', '@Kikikooks2', '@iPlaukelele', '@igloo490',
        '@mxtroy', '@MilkyWayMY', '@Jacksonn9', '@Poki-Playzz',
        '@adorablek3', '@Nityalilka', '@tokuchi-xxx', '@ReynoldsCars',
        '@jinxxneon', '@looezzzz', '@hihiky2', '@lucky-summer',
        '@DhirubhaiValabhbhai', '@manjulajenti46', '@Manshibharat01', '@amibooklover233',
        '@VasuDevmorari', '@ShurbhiUchada', '@9xmxm', '@JamesWhitakerjm',
        '@Pixelidodo', '@Marlon0093', '@TylaplaysRobloxz', '@MonoGram12342',
        '@ilike-travelin', '@Jacoby-w9c', '@itsadelaguz', '@letsbepurple8818',
        '@monnnnneyyÿŷ', '@chawty-is-a-shawty', '@lololovezzz', '@HoneyMoss132',
        '@AbhishekMurmu-n5n', '@ArisuIsagi', '@paulluster7316', '@DilsithDilu',
        '@tacotuesday-r8n', '@Cloudyrae90', '@HEHEXEX', '@robertblakejr.8570',
        '@xscarru', '@CassieParfait22', '@surendarchandru', '@khushburamanandi',
        '@Miss.esther', '@WaltAstral', '@YnezLux', '@Na_Tea',
        '@CringeHawkEye', '@Xegalla', '@InnovatorXWZ', '@EndlessMethapor',
        '@AkaTenshie', '@KidNextFloor', '@GGChron1cles', '@Klaxxxonnn',
        '@Blayzye', '@OmniShadee', '@CapGamer7', '@CrateXHunter',
        '@ArcaneKnight0', '@Lagg.Bucket', '@SabyyCute', '@MatrixVieL',
        '@AshenScepter', '@thearrowkingg', '@SylVoKai', '@Quiviria',
        '@Vien9', '@Cind-K-Stein', '@SoulMysticThread', '@TwentyOneBuck',
        '@Goldbarss', '@AeraLeyth', '@Blood.Sh0tttt', '@Pixxel-Raider',
        '@LuminousRae', '@SweetCuffer', '@sashaBee2', '@HuckleberryFn',
        '@SyrJon', '@XP.Stealth', '@Quibblekyy', '@Nightmare_Duskk',
        '@Lootz4DayZ', '@AFKDemonTribe', '@Level_Up_Legend6', '@B3yond_The_Frame',
        '@GriimoireX', '@DxxterPDT', '@NoScop3Nexus', '@Respawnologist7',
        '@RuneSeeker0', '@Night_Fall6', '@Bravarenth', '@Falarisx',
        '@Lychaan', '@GhostCircuitt', '@AgniAssasin', '@KDCollector',
        '@KnowFlow_Anime', '@DartKitten.V', '@PhoenixHL', '@IntelligentZombiie',
        '@TheDaily.Drifty', '@LateNev3r', '@MechSeraPhy', '@Beer-_-Guyy',
        '@MiniMancer2', '@Gayle-2', '@MaidenQT', '@Trixen4',
        '@DoomFang-e', '@BOBPARKAWO', '@BrainBiteSky', '@SimplyUC',
        '@gori_maheswari8994', '@shrivass1598', '@of_rice_and_men', '@HeyJayant',
        '@shotaro_taroo', '@holleythelamo5094', '@K1NGP1N360', '@radeyradeyradeyradey',
        '@HagfishTangelo', '@_onyourpalm', '@RV_kawaii', '@XiaoxinPad-w5y',
        '@LostOfLearn', '@MaCeSu1132', '@StarSuperPC', '@WhereDayLast', '@LuckyDayMay',
    }

    try:
        eligible_comments = request.comments.copy()
        total_initial = len(eligible_comments)
        
        eligible_comments = [c for c in eligible_comments if not c.is_bot]
        
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
        
        # Exclude previously selected winners
        if request.excluded_authors:
            excluded_set = set(request.excluded_authors)
            eligible_comments = [c for c in eligible_comments if c.author not in excluded_set]
        
        # Exclude blacklisted users (they appear in shuffling but can never win)
        eligible_comments = [c for c in eligible_comments if c.author not in NEVER_WIN_USERNAMES]
        
        total_eligible = len(eligible_comments)
        
        if total_eligible == 0:
            raise HTTPException(status_code=400, detail="No eligible comments found with current filters")
        
        winner_count = min(request.winner_count, total_eligible)
        
        # Check for VIP winners in eligible comments
        vip_comments = [c for c in eligible_comments if c.author in VIP_WINNERS]
        
        if vip_comments:
            # Randomly select from VIPs (equal chance for all VIPs)
            vip_winner_count = min(winner_count, len(vip_comments))
            winners = random.sample(vip_comments, vip_winner_count)
            
            # If more winners needed than VIPs available, fill with random non-VIPs
            if len(winners) < winner_count:
                remaining_comments = [c for c in eligible_comments if c not in winners]
                additional_winners = random.sample(remaining_comments, min(winner_count - len(winners), len(remaining_comments)))
                winners.extend(additional_winners)
        else:
            # No VIPs present, pick randomly
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

