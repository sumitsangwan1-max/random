import { useState } from "react";
import "@/App.css";
import axios from "axios";
import { Youtube, Filter, Shuffle, Download, Trophy, Users, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [videoUrl, setVideoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [videoInfo, setVideoInfo] = useState(null);
  const [comments, setComments] = useState([]);
  const [botsDetected, setBotsDetected] = useState(0);
  const [excludeDuplicates, setExcludeDuplicates] = useState(true);
  const [keywordFilter, setKeywordFilter] = useState("");
  const [winnerCount, setWinnerCount] = useState(1);
  const [winners, setWinners] = useState([]);
  const [stats, setStats] = useState(null);
  const [shuffling, setShuffling] = useState(false);
  const [shufflingWinners, setShufflingWinners] = useState([]);
  const [previousWinners, setPreviousWinners] = useState([]);  // Track all previous winners
  const [showTerms, setShowTerms] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  const fetchComments = async () => {
    if (!videoUrl.trim()) {
      toast.error("Please enter a YouTube video URL");
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/youtube/fetch-comments`, {
        video_url: videoUrl
      });
      
      setVideoInfo(response.data.video_info);
      setComments(response.data.comments);
      setBotsDetected(response.data.bots_detected);
      setWinners([]);
      setPreviousWinners([]);  // Reset previous winners for new video
      setStats(null);
      toast.success(`Fetched ${response.data.total_comments} comments successfully!`);
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to fetch comments");
    } finally {
      setLoading(false);
    }
  };

  const pickWinners = async () => {
  if (comments.length === 0) {
    toast.error("Please fetch comments first");
    return;
  }

  setShuffling(true);
  setWinners([]);              // clear previous winners
  setShufflingWinners([]);     // reset shuffle display

  // start shuffle animation
  const shuffleInterval = setInterval(() => {
    const randomComments = [];
    const count = parseInt(winnerCount, 10);

    for (let i = 0; i < count; i++) {
      const randomIndex = Math.floor(Math.random() * comments.length);
      randomComments.push(comments[randomIndex]);
    }

    setShufflingWinners(randomComments);
  }, 150);

  // after 3 seconds, pick real winners
  setTimeout(async () => {
    clearInterval(shuffleInterval);

    try {
     const response = await axios.post(`${API}/youtube/pick-winners`, {
          comments: comments,
          exclude_duplicates: excludeDuplicates,
          keyword_filter: keywordFilter,
          winner_count: parseInt(winnerCount),
          excluded_authors: previousWinners  // Exclude previous winners
        });
        
        setShufflingWinners([]);
        setWinners(response.data.winners);
        // Add new winners to previous winners list
        setPreviousWinners(prev => [...prev, ...response.data.winners.map(w => w.author)]);
        setStats({
        total_eligible: response.data.total_eligible,
        total_filtered: response.data.total_filtered
      });

      toast.success(`Selected ${response.data.winners.length} winner(s)!`);
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to pick winners");
    } finally {
      setShuffling(false);
    }
  }, 3000);
};

  const exportWinners = () => {
    if (winners.length === 0) {
      toast.error("No winners to export");
      return;
    }

    const csv = [
      ['Author', 'Comment', 'Published At', 'Like Count'],
      ...winners.map(w => [
        w.author,
        w.text.replace(/"/g, '""'),
        w.published_at,
        w.like_count
      ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `winners-${new Date().getTime()}.csv`;
    a.click();
    toast.success("Winners exported successfully!");
  };

  return (
    <div className="min-h-screen bg-background noise-texture">
      <Toaster position="top-right" />
    {/* Global Loading Overlay */}
{loading && (
  <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center">
    <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center shadow-xl">
      <div className="mb-4 flex justify-center">
        <div className="animate-spin-slow text-4xl">⚡</div>
      </div>
      <h2 className="font-heading text-2xl font-bold mb-3">
        Scanning for Bot Activity
      </h2>
      <p className="text-muted-foreground text-sm leading-relaxed">
        Waking up server and scanning comments for bot activity.<br />
        This may take up to <strong>1–2 minutes</strong> on first request.<br />
        Please do not refresh or close the page.
      </p>
    </div>
  </div>
)}

      
      <div className="hero-glow absolute top-0 left-0 right-0 h-96 pointer-events-none" />
      
      <div className="relative max-w-7xl mx-auto p-6 md:p-12 lg:p-24">
        <header className="text-center mb-12 md:mb-20">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 border border-primary/20 mb-6">
            <Youtube className="w-8 h-8 text-primary" />
          </div>
          <h1 className="font-heading font-extrabold text-5xl md:text-7xl tracking-tight leading-none mb-4">
            YouTube Comment Picker
          </h1>
          <p className="font-body text-base text-muted-foreground leading-relaxed max-w-2xl mx-auto">
            Pick random winners from YouTube comments for your giveaways & filter BOTS. Fair, transparent, and instant.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          <Card className="lg:col-span-8 glass-card border-white/10">
            <CardHeader>
              <CardTitle className="font-heading text-2xl flex items-center gap-2">
                <Youtube className="w-5 h-5 text-primary" />
                Video URL
              </CardTitle>
              <CardDescription>Enter the YouTube video URL to fetch comments</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Input
                  data-testid="video-url-input"
                  type="text"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  className="bg-gray-50 border-2 border-gray-200 focus:border-primary/50 text-xl p-8 rounded-2xl font-mono"
                  onKeyPress={(e) => e.key === 'Enter' && fetchComments()}
                />
              </div>
              <Button
                data-testid="fetch-comments-btn"
                onClick={fetchComments}
                disabled={loading}
                className="w-full bg-primary text-white hover:bg-primary/90 shadow-[0_0_20px_rgba(255,0,51,0.3)] hover:scale-105 font-bold tracking-wide px-8 py-6 rounded-full h-auto text-lg"
              >
                {loading ? (
                  <>
                    <div className="animate-spin-slow mr-2">⚡</div>
                    Fetching Comments...
                  </>
                ) : (
                  "Fetch Comments"
                )}
              </Button>
            </CardContent>
          </Card>

          <div className="lg:col-span-4 space-y-4">
            <Card className="glass-card border-white/10">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-primary" />
                  Comments
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-heading font-bold">
                  {comments.length.toLocaleString()}
                </div>
                <div className="text-sm text-muted-foreground font-mono">Total Fetched</div>
              </CardContent>
            </Card>

            <Card className="glass-card border-white/10">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Filter className="w-4 h-4 text-primary" />
                  BOT Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-heading font-bold text-yellow-500">
                  {botsDetected}
                </div>
                <div className="text-sm text-muted-foreground font-mono">BOTS Detected</div>
              </CardContent>
            </Card>

            <Card className="glass-card border-white/10">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Trophy className="w-4 h-4 text-primary" />
                  Winners
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-heading font-bold text-primary">
                  {winners.length}
                </div>
                <div className="text-sm text-muted-foreground font-mono">Selected</div>
              </CardContent>
            </Card>
          </div>
        </div>

        {videoInfo && (
          <Card className="glass-card border-white/10 mb-8" data-testid="video-info-card">
            <CardContent className="p-6">
              <div className="flex gap-6 items-start">
                <img 
                  src={videoInfo.thumbnail_url} 
                  alt={videoInfo.title}
                  className="w-40 h-24 object-cover rounded-lg border border-white/10"
                />
                <div className="flex-1">
                  <h3 className="font-heading font-semibold text-xl mb-2">{videoInfo.title}</h3>
                  <p className="text-muted-foreground text-sm mb-3">{videoInfo.channel_title}</p>
                  <div className="flex gap-6 text-sm font-mono">
                    <span>{parseInt(videoInfo.view_count).toLocaleString()} views</span>
                    <span>{parseInt(videoInfo.like_count).toLocaleString()} likes</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {comments.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
            <Card className="lg:col-span-5 glass-card border-white/10">
              <CardHeader>
                <CardTitle className="font-heading text-2xl flex items-center gap-2">
                  <Filter className="w-5 h-5 text-primary" />
                  Filters
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="font-mono text-xs uppercase tracking-widest text-muted-foreground/70">Exclude Duplicates</Label>
                    <p className="text-sm text-muted-foreground mt-1">One entry per user</p>
                  </div>
                  <Switch
                    data-testid="exclude-duplicates-switch"
                    checked={excludeDuplicates}
                    onCheckedChange={setExcludeDuplicates}
                  />
                </div>

                <div className="space-y-2">
                  <Label className="font-mono text-xs uppercase tracking-widest text-muted-foreground/70">Keyword Filter</Label>
                  <Input
                    data-testid="keyword-filter-input"
                    type="text"
                    placeholder="keyword1, keyword2"
                    value={keywordFilter}
                    onChange={(e) => setKeywordFilter(e.target.value)}
                    className="bg-gray-50 border-2 border-gray-200 focus:border-primary/50 text-lg p-4 rounded-2xl font-mono"

                  />
                  <p className="text-xs text-muted-foreground">Comma-separated keywords to filter comments</p>
                </div>

                <div className="space-y-2">
                  <Label className="font-mono text-xs uppercase tracking-widest text-muted-foreground/70">Number of Winners</Label>
                  <Input
                    data-testid="winner-count-input"
                    type="number"
                    min="1"
                    value={winnerCount}
                    onChange={(e) => setWinnerCount(e.target.value)}
                    className="bg-gray-50 border-2 border-gray-200 focus:border-primary/50 text-lg p-4 rounded-2xl font-mono"

                  />
                </div>

                <Button
                  data-testid="pick-winners-btn"
                  onClick={pickWinners}
                  disabled={shuffling}
                  className="w-full bg-primary text-white hover:bg-primary/90 shadow-[0_0_20px_rgba(255,0,51,0.3)] hover:scale-105 font-bold tracking-wide px-8 py-6 rounded-full h-auto"
                >
                  {shuffling ? (
                    <>
                      <Shuffle className="w-5 h-5 mr-2 animate-spin-slow" />
                      Shuffling...
                    </>
                  ) : (
                    <>
                      <Shuffle className="w-5 h-5 mr-2" />
                      Pick Winners
                    </>
                  )}
                </Button>

                {stats && (
                  <div className="pt-4 border-t border-white/10 space-y-2 text-sm font-mono">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Eligible Comments:</span>
                      <span className="text-foreground font-medium">{stats.total_eligible}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Filtered Out:</span>
                      <span className="text-foreground font-medium">{stats.total_filtered}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

     <div className="lg:col-span-7">
  {shuffling && shufflingWinners.length > 0 ? (
    <Card className="glass-card border-primary/30">
      <CardHeader>
        <CardTitle className="font-heading text-2xl flex items-center gap-2">
          <Shuffle className="w-6 h-6 text-primary animate-spin-slow" />
          Shuffling...
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {shufflingWinners.map((participant, index) => (
            <div
              key={index}
              className="winner-card p-6 rounded-lg shuffle-animation"
            >
              <div className="flex items-start gap-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center border border-primary/40">
                    <span className="text-primary font-bold text-xl">#{index + 1}</span>
                  </div>
                  {participant.author_profile_image_url && (
                    <img 
                      src={participant.author_profile_image_url}
                      alt={participant.author}
                      className="w-12 h-12 rounded-full border-2 border-white/10"
                    />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-heading font-semibold text-lg text-primary/70">{participant.author}</h4>
                    <span className="text-xs font-mono text-muted-foreground">❤️ {participant.like_count}</span>
                  </div>
                  <p className="text-muted-foreground text-sm mb-2 line-clamp-2">{participant.text}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  ) : winners.length > 0 ? (
    <Card className="glass-card border-primary/30">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="font-heading text-2xl flex items-center gap-2">
            <Trophy className="w-6 h-6 text-primary" />
            Winners
          </CardTitle>
          <Button
            data-testid="export-btn"
            onClick={exportWinners}
            variant="outline"
            className="border-white/10 hover:border-white/20 rounded-full"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {winners.map((winner, index) => (
            <div
              key={index}
              data-testid={`winner-${index}`}
              className="winner-card p-6 rounded-lg winner-reveal"
            >
              <div className="flex items-start gap-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center border border-primary/40">
                    <span className="text-primary font-bold text-xl">#{index + 1}</span>
                  </div>
                  {winner.author_profile_image_url && (
                    <img 
                      src={winner.author_profile_image_url}
                      alt={winner.author}
                      className="w-12 h-12 rounded-full border-2 border-white/10"
                    />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {winner.author_channel_url ? (
                      <a
                        href={winner.author_channel_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => {
                          e.preventDefault();
                          const link = document.createElement('a');
                          link.href = winner.author_channel_url;
                          link.target = '_blank';
                          link.rel = 'noopener noreferrer';
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }}
                        className="font-heading font-semibold text-lg text-primary hover:text-primary/80 hover:underline cursor-pointer transition-all duration-200"
                        data-testid={`winner-${index}-channel-link`}
                      >
                        {winner.author}
                      </a>
                    ) : (
                      <h4 className="font-heading font-semibold text-lg">{winner.author}</h4>
                    )}
                    <span className="text-xs font-mono text-muted-foreground">❤️ {winner.like_count}</span>
                  </div>
                  <p className="text-muted-foreground text-sm mb-2">{winner.text}</p>
                  <p className="text-xs font-mono text-muted-foreground/50">
                    {new Date(winner.published_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  ) : (
    <Card className="glass-card border-white/10 h-full flex items-center justify-center min-h-[400px]">
      <CardContent className="text-center">
        <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Trophy className="w-10 h-10 text-primary/50" />
        </div>
        <h3 className="font-heading text-xl text-muted-foreground mb-2">No Winners Yet</h3>
        <p className="text-sm text-muted-foreground/70">Click "Pick Winners" to randomly select from comments</p>
      </CardContent>
    </Card>
  )}
</div>
          </div>
        )}

        {!videoInfo && comments.length === 0 && (
          <Card className="glass-card border-white/10 text-center py-20">
            <CardContent>
              <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                <Youtube className="w-12 h-12 text-primary/50" />
              </div>
              <h3 className="font-heading text-2xl text-muted-foreground mb-3">Get Started</h3>
              <p className="text-muted-foreground/70 max-w-md mx-auto">
                Enter a YouTube video URL above to fetch comments and start picking winners for your giveaway.
              </p>
            </CardContent>
          </Card>
        )}
{/* Disclaimer */}
<footer className="mt-20 pt-8 pb-12 border-t border-white/10">
  <div className="max-w-7xl mx-auto px-6 text-center">
    <h3 className="font-heading font-bold text-lg mb-1">
      Random Comment Picker
    </h3>
    <p className="text-sm text-muted-foreground mb-4">
      Fair & transparent YouTube giveaway tool
    </p>

    <div className="flex justify-center gap-6 text-sm mb-4">
      <button
  onClick={() => setShowTerms(true)}
  className="text-muted-foreground hover:text-primary cursor-pointer"
>
  Terms of Service
</button>

<button
  onClick={() => setShowPrivacy(true)}
  className="text-muted-foreground hover:text-primary cursor-pointer"
>
  Privacy Policy
</button>

<button
  onClick={() => setShowDisclaimer(true)}
  className="text-muted-foreground hover:text-primary cursor-pointer"
>
  Disclaimer
</button>

    </div>

    <p className="text-xs text-muted-foreground">
      © {new Date().getFullYear()} Random Comment Picker. All rights reserved.
    </p>
  </div>
</footer>

      {/* Terms of Service Modal */}
        {showTerms && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowTerms(false)}>
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-8" onClick={(e) => e.stopPropagation()}>
              <h2 className="font-heading font-bold text-3xl mb-4">Terms of Service</h2>
              <div className="space-y-4 text-sm text-muted-foreground">
                <p><strong>Last Updated:</strong> {new Date().toLocaleDateString()}</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">1. Acceptance of Terms</h3>
                <p>By accessing and using Random Comment Picker, you agree to be bound by these Terms of Service.</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">2. Use of Service</h3>
                <p>This service is provided &quot;as is&quot; for selecting random winners from YouTube comments. You must:</p>
                <ul className="list-disc ml-6">
                  <li>Provide your own YouTube API key</li>
                  <li>Comply with YouTube&apos;s Terms of Service</li>
                  <li>Use the service fairly and lawfully</li>
                  <li>Not attempt to manipulate or game the selection process</li>
                </ul>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">3. API Usage</h3>
                <p>You are responsible for your YouTube API key usage and quotas. We are not liable for API quota exhaustion or costs.</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">4. Limitation of Liability</h3>
                <p>Random Comment Picker is provided without warranties. We are not responsible for winner selection disputes or technical issues.</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">5. Changes to Terms</h3>
                <p>We reserve the right to modify these terms at any time. Continued use constitutes acceptance of modified terms.</p>
              </div>
              <button
                onClick={() => setShowTerms(false)}
                className="mt-6 bg-primary text-white px-6 py-3 rounded-full hover:bg-primary/90 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Privacy Policy Modal */}
        {showPrivacy && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowPrivacy(false)}>
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-8" onClick={(e) => e.stopPropagation()}>
              <h2 className="font-heading font-bold text-3xl mb-4">Privacy Policy</h2>
              <div className="space-y-4 text-sm text-muted-foreground">
                <p><strong>Last Updated:</strong> {new Date().toLocaleDateString()}</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">1. Information We Collect</h3>
                <p>Random Comment Picker collects minimal information:</p>
                <ul className="list-disc ml-6">
                  <li>YouTube video URLs you provide</li>
                  <li>Comments fetched via YouTube API (temporarily processed)</li>
                  <li>No personal information is stored permanently</li>
                </ul>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">2. How We Use Information</h3>
                <p>Information is used solely for:</p>
                <ul className="list-disc ml-6">
                  <li>Fetching comments from YouTube videos</li>
                  <li>Filtering and selecting random winners</li>
                  <li>Displaying results to you</li>
                </ul>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">3. Data Storage</h3>
                <p>We do not permanently store:</p>
                <ul className="list-disc ml-6">
                  <li>YouTube comments</li>
                  <li>Winner information</li>
                  <li>User personal data</li>
                </ul>
                <p>All data is processed in real-time and discarded after session ends.</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">4. Third-Party Services</h3>
                <p>This service uses YouTube Data API. YouTube&apos;s privacy policy applies to data fetched from their platform.</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">5. Your API Key</h3>
                <p>Your YouTube API key is used only for your requests and is not shared or stored on our servers.</p>
              </div>
              <button
                onClick={() => setShowPrivacy(false)}
                className="mt-6 bg-primary text-white px-6 py-3 rounded-full hover:bg-primary/90 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Disclaimer Modal */}
        {showDisclaimer && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowDisclaimer(false)}>
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-8" onClick={(e) => e.stopPropagation()}>
              <h2 className="font-heading font-bold text-3xl mb-4">Disclaimer</h2>
              <div className="space-y-4 text-sm text-muted-foreground">
                <p><strong>Last Updated:</strong> {new Date().toLocaleDateString()}</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">No Guarantee of Results</h3>
                <p>Random Comment Picker provides a tool for random selection but does not guarantee:</p>
                <ul className="list-disc ml-6">
                  <li>Accuracy of winner selection</li>
                  <li>Complete removal of all bot accounts</li>
                  <li>Uninterrupted service availability</li>
                  <li>Compatibility with all YouTube videos</li>
                </ul>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">User Responsibility</h3>
                <p>Users are responsible for:</p>
                <ul className="list-disc ml-6">
                  <li>Verifying winner authenticity</li>
                  <li>Complying with YouTube Terms of Service</li>
                  <li>Following applicable giveaway laws and regulations</li>
                  <li>Managing their own YouTube API quotas and costs</li>
                  <li>Resolving any disputes with winners or participants</li>
                </ul>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">Bot Detection Limitations</h3>
                <p>While we attempt to filter bot accounts, no automated system is perfect. Users should manually verify winners if needed.</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">Third-Party Content</h3>
                <p>Comments and user data are provided by YouTube. We are not responsible for the content or accuracy of third-party information.</p>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">Legal Compliance</h3>
                <p>Users must ensure their giveaways comply with:</p>
                <ul className="list-disc ml-6">
                  <li>Local laws and regulations</li>
                  <li>YouTube&apos;s policies and guidelines</li>
                  <li>Contest and sweepstakes laws</li>
                  <li>Tax reporting requirements</li>
                </ul>
                
                <h3 className="font-semibold text-foreground text-lg mt-6">No Warranty</h3>
                <p>This service is provided &quot;AS IS&quot; without any warranties, express or implied. Use at your own risk.</p>
              </div>
              <button
                onClick={() => setShowDisclaimer(false)}
                className="mt-6 bg-primary text-white px-6 py-3 rounded-full hover:bg-primary/90 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
