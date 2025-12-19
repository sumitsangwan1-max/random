
Action: file_editor str_replace /app/frontend/src/App.js --old-str "            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default App;" --new-str "            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <footer className=\"mt-20 pt-8 pb-12 border-t border-gray-200\">
          <div className=\"max-w-7xl mx-auto px-6 md:px-12\">
            <div className=\"flex flex-col md:flex-row justify-between items-center gap-6\">
              <div className=\"text-center md:text-left\">
                <h3 className=\"font-heading font-bold text-lg mb-2\">Random Comment Picker</h3>
                <p className=\"text-sm text-muted-foreground\">Fair & transparent YouTube giveaway tool</p>
              </div>
              
              <div className=\"flex flex-wrap justify-center gap-6 text-sm\">
                <button
                  onClick={() => setShowTerms(true)}
                  className=\"text-muted-foreground hover:text-primary transition-colors cursor-pointer\"
                >
                  Terms of Service
                </button>
                <button
                  onClick={() => setShowPrivacy(true)}
                  className=\"text-muted-foreground hover:text-primary transition-colors cursor-pointer\"
                >
                  Privacy Policy
                </button>
                <button
                  onClick={() => setShowDisclaimer(true)}
                  className=\"text-muted-foreground hover:text-primary transition-colors cursor-pointer\"
                >
                  Disclaimer
                </button>
              </div>
            </div>
            
            <div className=\"text-center mt-6 text-xs text-muted-foreground\">
              © {new Date().getFullYear()} Random Comment Picker. All rights reserved.
            </div>
          </div>
        </footer>

        {/* Terms of Service Modal */}
        {showTerms && (
          <div className=\"fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50\" onClick={() => setShowTerms(false)}>
            <div className=\"bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-8\" onClick={(e) => e.stopPropagation()}>
              <h2 className=\"font-heading font-bold text-3xl mb-4\">Terms of Service</h2>
              <div className=\"space-y-4 text-sm text-muted-foreground\">
                <p><strong>Last Updated:</strong> {new Date().toLocaleDateString()}</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">1. Acceptance of Terms</h3>
                <p>By accessing and using Random Comment Picker, you agree to be bound by these Terms of Service.</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">2. Use of Service</h3>
                <p>This service is provided \"as is\" for selecting random winners from YouTube comments. You must:</p>
                <ul className=\"list-disc ml-6\">
                  <li>Provide your own YouTube API key</li>
                  <li>Comply with YouTube's Terms of Service</li>
                  <li>Use the service fairly and lawfully</li>
                  <li>Not attempt to manipulate or game the selection process</li>
                </ul>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">3. API Usage</h3>
                <p>You are responsible for your YouTube API key usage and quotas. We are not liable for API quota exhaustion or costs.</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">4. Limitation of Liability</h3>
                <p>Random Comment Picker is provided without warranties. We are not responsible for winner selection disputes or technical issues.</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">5. Changes to Terms</h3>
                <p>We reserve the right to modify these terms at any time. Continued use constitutes acceptance of modified terms.</p>
              </div>
              <button
                onClick={() => setShowTerms(false)}
                className=\"mt-6 bg-primary text-white px-6 py-3 rounded-full hover:bg-primary/90 transition-all\"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Privacy Policy Modal */}
        {showPrivacy && (
          <div className=\"fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50\" onClick={() => setShowPrivacy(false)}>
            <div className=\"bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-8\" onClick={(e) => e.stopPropagation()}>
              <h2 className=\"font-heading font-bold text-3xl mb-4\">Privacy Policy</h2>
              <div className=\"space-y-4 text-sm text-muted-foreground\">
                <p><strong>Last Updated:</strong> {new Date().toLocaleDateString()}</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">1. Information We Collect</h3>
                <p>Random Comment Picker collects minimal information:</p>
                <ul className=\"list-disc ml-6\">
                  <li>YouTube video URLs you provide</li>
                  <li>Comments fetched via YouTube API (temporarily processed)</li>
                  <li>No personal information is stored permanently</li>
                </ul>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">2. How We Use Information</h3>
                <p>Information is used solely for:</p>
                <ul className=\"list-disc ml-6\">
                  <li>Fetching comments from YouTube videos</li>
                  <li>Filtering and selecting random winners</li>
                  <li>Displaying results to you</li>
                </ul>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">3. Data Storage</h3>
                <p>We do not permanently store:</p>
                <ul className=\"list-disc ml-6\">
                  <li>YouTube comments</li>
                  <li>Winner information</li>
                  <li>User personal data</li>
                </ul>
                <p>All data is processed in real-time and discarded after session ends.</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">4. Third-Party Services</h3>
                <p>This service uses YouTube Data API. YouTube's privacy policy applies to data fetched from their platform.</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">5. Your API Key</h3>
                <p>Your YouTube API key is used only for your requests and is not shared or stored on our servers.</p>
              </div>
              <button
                onClick={() => setShowPrivacy(false)}
                className=\"mt-6 bg-primary text-white px-6 py-3 rounded-full hover:bg-primary/90 transition-all\"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Disclaimer Modal */}
        {showDisclaimer && (
          <div className=\"fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50\" onClick={() => setShowDisclaimer(false)}>
            <div className=\"bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-8\" onClick={(e) => e.stopPropagation()}>
              <h2 className=\"font-heading font-bold text-3xl mb-4\">Disclaimer</h2>
              <div className=\"space-y-4 text-sm text-muted-foreground\">
                <p><strong>Last Updated:</strong> {new Date().toLocaleDateString()}</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">No Guarantee of Results</h3>
                <p>Random Comment Picker provides a tool for random selection but does not guarantee:</p>
                <ul className=\"list-disc ml-6\">
                  <li>Accuracy of winner selection</li>
                  <li>Complete removal of all bot accounts</li>
                  <li>Uninterrupted service availability</li>
                  <li>Compatibility with all YouTube videos</li>
                </ul>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">User Responsibility</h3>
                <p>Users are responsible for:</p>
                <ul className=\"list-disc ml-6\">
                  <li>Verifying winner authenticity</li>
                  <li>Complying with YouTube Terms of Service</li>
                  <li>Following applicable giveaway laws and regulations</li>
                  <li>Managing their own YouTube API quotas and costs</li>
                  <li>Resolving any disputes with winners or participants</li>
                </ul>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">Bot Detection Limitations</h3>
                <p>While we attempt to filter bot accounts, no automated system is perfect. Users should manually verify winners if needed.</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">Third-Party Content</h3>
                <p>Comments and user data are provided by YouTube. We are not responsible for the content or accuracy of third-party information.</p>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">Legal Compliance</h3>
                <p>Users must ensure their giveaways comply with:</p>
                <ul className=\"list-disc ml-6\">
                  <li>Local laws and regulations</li>
                  <li>YouTube's policies and guidelines</li>
                  <li>Contest and sweepstakes laws</li>
                  <li>Tax reporting requirements</li>
                </ul>
                
                <h3 className=\"font-semibold text-foreground text-lg mt-6\">No Warranty</h3>
                <p>This service is provided \"AS IS\" without any warranties, express or implied. Use at your own risk.</p>
              </div>
              <button
                onClick={() => setShowDisclaimer(false)}
                className=\"mt-6 bg-primary text-white px-6 py-3 rounded-full hover:bg-primary/90 transition-all\"
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

export default App;"
Observation: String replacement failed: No replacement was performed, `old_str` did not appear verbatim in /app/frontend/src/App.js.
