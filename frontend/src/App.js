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
      setWinners([]);
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
    
    setTimeout(async () => {
      try {
        const response = await axios.post(`${API}/youtube/pick-winners`, {
          comments: comments,
          exclude_duplicates: excludeDuplicates,
          keyword_filter: keywordFilter,
          winner_count: parseInt(winnerCount)
        });
        
        setWinners(response.data.winners);
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
    }, 1500);
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
                  className="bg-black/50 border-2 border-white/10 focus:border-primary/50 text-xl p-8 rounded-2xl font-mono"
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
                    className="bg-black/50 border-white/10 focus:border-primary/50 rounded-lg"
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
                    className="bg-black/50 border-white/10 focus:border-primary/50 rounded-lg"
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
              {winners.length > 0 ? (
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
                            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center border border-primary/40">
                              <span className="text-primary font-bold text-xl">#{index + 1}</span>
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="font-heading font-semibold text-lg">{winner.author}</h4>
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
      </div>
    </div>
  );
}

export default App;