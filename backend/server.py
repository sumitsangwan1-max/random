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
    """Extract video ID from YouTube URL (supports Shorts)"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        r'(?:youtu\.be\/)([\w-]+)',
        r'(?:youtube\.com\/embed\/)([\w-]+)',
        r'(?:youtube\.com\/v\/)([\w-]+)',
        r'(?:youtube\.com\/shorts\/)([\w-]+)'  # ✅ Shorts support
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Direct video ID (11 chars)
    if len(url) == 11 and re.match(r'^[\w-]+$', url):
        return url
    
    raise ValueError("Invalid YouTube URL")

def is_bot_comment(author: str, text: str) -> bool:
    """Detect bot comments from blacklisted usernames"""
    bot_usernames = {
        '@tylernoahanderson1997', '@Louis-Vincent-Myers', '@Randy.James.Harris',
        '@terrybrown1977', '@austinward23', '@JoshuaEthanCook',
        '@Jeffrey-Jose-Roberts', '@zacharyloganortiz1973', '@subho-v5s', '@Subscribergoat', '@Aryansenna', '@Brook-k6d',
'@jecobchristia', '@timseifart-s2p', '@Producer-p8l4y', '@VibeVisionary-y2z', '@gwagonat', '@Cricket-l4c', '@Frazer-s2z',
'@Luck-w2q', '@MarvinagmesMarvinagnes', '@russmoore-m.2h', '@yenwallz', '@project-o8e', '@jaken-s1l', '@MaCeSu1132', '@StarSuperPC', '@WhereDayLast', '@LuckyDayMay', '@SANDESHGAMERS97',
'@SagarSagarji-j3b', '@PhilipCharles-y9k', '@KkkJjj-j4u', '@dusabemunguadeline2848', '@MG_SUHEL_LIVE',
'@MichaelDehinsilu-w5y', '@المغااامر', '@vinodsir2125', '@Mitti_Di_Awaaz', '@ZainabchZainabch-p8y', '@NassirHabb', '@Siyaaaa1', '@Pro_Rayyan1',
'@RamlalSharma-wh6gc', '@Yaari-ep9us', '@Hottest_x_Trends', '@LealGreen', '@LaisDays', '@WhatDeal-h6j', '@DayLoad-k7t', '@LasLoMail', 
'@Ammiethebusygirl', '@Blessingewornam', '@Christinahappiness',
'@Christianazayn', '@Clarkefaithtashalee', '@Diaryofagoodfoodlover',
'@Emweeson', '@Fernandezhermes', '@JaneAudith', '@luandalove',
'@Monalisawealth', '@Iconiccruz',
'@Mbalijohnson', '@Zayybee', '@Duchess607', '@Cindysteeze', '@blessedaurora', '@Eugene_Douglas_Bennett', '@Gabriel_Ralph_Hall', '@PeterFrankBrooks', '@AlbertMartinez_1739',
'@PaulPaulCook', '@christianpeterson1992', '@CharlesJackWhite_6029',
'@stevenedwardwood74', '@TimothyRichardson_7194', '@EugenePeterson_3921',
'@quynhlucnhu5152', '@brWianwalker', '@josegregorylewis1959',
'@Brandon-Samuel-Wright', '@aaronFruiz', '@ZacharyGaryGray.8825',
'@stevenscottlee1976', '@DinhTa-zt2we', '@KimPhungy9n8pa_325',
'@peterbrooks1973', '@MinhHoaaq8jk9_450', '@donaldstewart1991',
'@GregoryJamesWright', '@GiaBaoa8pucz_908', '@seanrZoss', '@mikisoobin',
'@eilyu', '@nyc5338', '@j_yeet', '@foodiefodder',
'@pizza443', '@lowaves27', '@bubbly1800', '@Na-triever',
'@yer16s', '@bubblegum9783', '@akshayramakrishnan', '@lotuspier5981',
'@guigun78', '@Ammm1233', '@shiningramrun', '@lerouge2331', '@BrianMorris_9415', '@adamchavez1961',
'@16daystildripmarketing93', '@therealotaku3874', '@G유서아', '@minan7754',
'@user-iz6tj9on2k', '@test6-t7h', '@niamagpie', '@marcingrail', '@jacelhy', '@moniger7', '@centralparksaga', '@dunknmoj', '@temmy1937', 
'@calwixx', '@AlecHuel', '@sakailansi', '@chase20cv', '@otisong', '@fingercutz', '@limpehuhlui', '@spyrocrow', '@maximuscts', '@gautim4u', 
'@donottech', '@jimmmm', '@lunaart09', '@MoenierHendricks-m5e', '@razaop3168', '@VictorHugo2526-p4n', '@KarolUyan-d8z', 
'@AngelesCarrillo-c8x', '@RaulGonzales-q2l', '@BraumPoro-x9k', '@Laura79367', '@Alfredo_nuñez', 
'@HumbertoGomez-k6l', '@pruebabienvenidamoneda', '@SantiagoInfa-r6w', '@MarthaCordero-b9v', 
 '@almejandro-q3r', '@CapsG2', '@MariannaParra-v9q', '@Josepachin-o7m', '@EmiliaGómezdeSandoval', 
'@Andres__Cordero-m3o', '@AnitaAramcito-o3b', '@arpit-18-a', '@nivesworx', '@steek96', '@grafire-j1o', '@EmiS11522', '@JayceArcane', 
'@DravenLap', '@AnaMar-o2k-m2g', '@Ateneoxd-x9b', '@RobertoPineda-w7i', '@glitchforgeat1',



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
    VIP_WINNERS = {'@Vanessa-y'}
    
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
        '@LostOfLearn', '@adadudud', '@Vishal-so3gk', '@Josegonzalez22-r7k', '@Nestormontenegro82', '@200mil6', 
        '@GuillermoFronk', '@InsideSay1212', '@RazerBladeZ3', '@RayTrayCube', '@LencyCyC1', '@CesloLos', '@Princessshayz',
        '@Shanethegreatness', '@StephCruzzie', '@Tuernylife', '@Valentinogeorgia', '@Winnerijay', '@nhanminh1447', '@PhilipDonaldCox', '@tienlam1770',
        '@EugeneBailey_9662', '@danielphilipallen1995', '@ralphwatWson', '@AustinMaryPerez', '@kevinbennett1972', 
'@TylerDennisChavez', '@larrychristianwilson18', '@CharlesWillieMorgan', '@haroldprice32',
'@raSndydylanmartinez', '@Nicholas.Johnny.Martinez', '@jamesjonathangonzalez1970', '@billybaker1974', '@ChadAnthonyVentures', '@Mendezz140', '@StephanieAg_',
'@Paulrichess', '@Naommey', '@AnitaSeweje', '@Charlotte_good', '@Demolzhappiness', '@Nengewilliams', '@Maamiserwaaa', '@Emmanuelwilz', '@Ginadenzel',
'@aishatmarcus', '@Moeta.b', '@LostOfLearn', '@Mikasload', '@leooghost', '@Mi-qm7ug', '@popa4810', '@Botiichal', '@astrodive', '@Hirrakit',
'@babi071', '@clover3854', '@chacha-ur6cb', '@Groovedude925', '@guillaumebarnabe998', '@Jack-i1v9c', '@music-kim1', '@audio--Bass-est',
'@scout-mortal', '@DriveXR-e5p', '@grafire-j1o', '@ann4501', '@tommyb9144', '@amora_kyros', '@slythy9', '@SUPERxGOKU',
'@Daxa-g1w', '@ForMusic-four', '@BigBaller989', '@maurya-1231', '@bryleewilliamson', '@starfire333', '@trini9352', 
'@aleczanny', '@andyliu313', '@dreamcatcher8574', '@Neko-wx3sk',
'@nicholas2040', '@giagg11', '@razaop3168', '@G전범지연', '@원-달-예린', '@공세아44', '@차-국-현아', 
'@MadeInLuke', '@pook-d5y', '@MikeStrangers-c1j', '@LPD-67', '@taescake', '@garnx', '@cortex4093',
'@shinku76', '@Sayee9007', '@blankedoit', '@Yufinn', '@Alex-wallzy', '@Zozorijo', '@charlynestyles', 
'@Carlos001-1', '@dunknmoj', '@daredevil-he', '@jinji_hi', '@fatu6357',
'@rmsaeed', '@fairyclo', '@bohu6o', '@KwanruetaiHee', '@rmbvlog6551', '@sarahkat26', '@LinhVu-jm8mu',
'@lanasotherland', '@silvivargas1426', '@BellaKT87', '@mteresaemond', '@seanleau', '@FigCloud', '@RavenRizz777',
'@jacenbarkoff', '@mizermira', '@shirazmarcel', '@devilselbow69', '@anaarevalo8425', '@therealpapparich', '@superguppyme',
'@Thatlakelife', '@oLi102', '@Ahdrea_B', '@maxiclarkson', '@megnifico', '@MrCollect', '@emmascore', '@BlogeyPiper', '@JmyladyHandcrafted', '@yenwallz', 
'@patticulver442', '@loyayyay', '@blureader1164', '@christinafredette8071', '@GOJ739', '@janetrivera1346', '@barbwolfrey1339', 
'@Mb-hdk-937', '@tray2811', '@maopoamy', '@googoobird', '@epiphx', '@lumerionOG',
'@Mabelosorio-s5o', '@MelissaGuzman-s2n', '@ricardomaster-q2l', '@mariaeugenia25-w6b', '@LudyRamirez-u3m', '@YolandaSopo-x4g', '@lunaart09', 
'@MoenierHendricks-m5e', '@VictorHugo2526-p4n', '@KarolUyan-d8z', '@AngelesCarrillo-c8x', '@RaulGonzales-q2l', '@BraumPoro-x9k', '@Laura79367', 
'@Alfredo_nuñez', '@HumbertoGomez-k6l', '@pruebabienvenidamoneda', '@SantiagoInfa-r6w', '@MarthaCordero-b9v', '@almejandro-q3r', '@CapsG2', 
'@MariannaParra-v9q', '@Josepachin-o7m', '@EmiliaGómezdeSandoval', '@Andres__Cordero-m3o', '@AnitaAramcito-o3b', '@BradyOP-u2e', '@edwardjuliansandoval8757', 
'@larrytravis', '@Gael40k', '@krad_slouds0', '@Hua770', '@ronniedadole7293', '@shirazmarcel', '@devilselbow69', '@therealpapparich', 
'@superguppyme', '@andrewdrill', '@teddybee69', '@flyguycruwear', '@JakeJonsen', '@cksteven76', '@Sunrise_in_April', '@artisanblades', 
'@u5fb', '@SiTiJaMuRmU05', '@Aprillovescats4ever90', '@Oats-y8x', '@Booklover889-l3y', '@A.M.sometimes', '@nivesworx', '@maxiclarkson', 
'@niamagpie', '@knivesnutz', '@marcingrail', '@garryyap', '@yolandiestre', '@courtnexD', '@andruroher', '@frankkgaming', '@yaleidysmargaritagonzalescarip', 
'@migueLdavidSilvaa', '@epicplayz2001', '@nicoIasfr7832', '@gonchuforexmx', '@elenaarg.8473', '@cecabrera5', '@rickyphineas5165', '@kellyrichard7295', '@juancruzferreira', 
'@lamaneracorrecta6044', '@gammesger', '@tedismithi', '@Carol-gc6kj', '@dshifflett806', '@YBABTU', '@rogerbee', '@matthnee', '@ciarasnoow', 
'@juanaviIa7388', '@natthveaz', '@marcohappyxD', '@befernando', '@markiiramos', '@paulwwong68', '@serenalove623', '@ommaticfim', '@lucialulu8392', 
'@catterinaborgogno', '@EricCRONy', '@chuiongamer', '@moxicau', '@stevemathie9683', '@harvviphps', '@shishitoedoo', '@redy2kI', '@RYBBwaker', 
'@Jessimirandas', '@daniicaidas', '@kariitox', '@katelynstamper9821', '@ronconnies6090', '@ericavelcover9065', '@kellymarker288', 
'@MrDahlia.', '@OliviaLenhart-i8i', '@Saantyda2', '@brissajcs', '@shirley4822', '@kimbberlyi', '@chiquikawaikpoper8357', 
'@Adriamnatosramon', '@Skryling', '@jakkecruz', '@driddesantos1762', '@adrians8024', '@jimmmm', '@micheel1958.', '@markstorete', 
'@Nehemiaslnvierte', '@biripochi9182', '@benjatam10', '@XQATR', '@karinaveracruz', '@Lilianaecliaceve', '@dorcassimon589', '@joseph18e', '@MarcoMorettig20', 
'@MatteoDeLuca-10', '@andresanchez343', '@shankzsxc', '@sebastiian9885', '@lorenzogento', '@markguenim9114', '@yeisonmartineez', '@brianhutchinson7683', 
'@moreenogua', '@DelmarClifton-u7n', '@laura_amydog', '@kimberlyholt3056', '@LisaDufault-q2l', '@Brook-k6d', '@markbriHanthompson', '@thanhhữu51', '@Eric-Jordan-Miller', 
'@fufuxia5' '@darrensmith9564', '@thymscd87', '@dancingdo.7', '@ann4501', '@Nahiiden', '@tsukisytcorner', '@maiionpar', '@j_yeet', '@foodiefodder',



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

