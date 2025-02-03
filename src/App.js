import React, { useState, useRef } from "react";
import { Globe, MessageSquare, Zap, Upload, Settings, Play, Youtube } from 'lucide-react';

function App() {
  const [videoFile, setVideoFile] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [uploadType, setUploadType] = useState("file"); // "file" or "youtube"
  const [language, setLanguage] = useState("en");
  const [captionOption, setCaptionOption] = useState("none");
  const [translatedVideo, setTranslatedVideo] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [videoSummary, setVideoSummary] = useState("");
  const [transcription, setTranscription] = useState("");

  // Refs for scroll functionality
  const featuresRef = useRef(null);
  const howItWorksRef = useRef(null);

  const scrollToSection = (ref) => {
    ref.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const languageOptions = [
    { label: "Arabic", value: "ar" },
    { label: "Chinese", value: "zh" },
    { label: "Dutch", value: "nl" },
    { label: "English", value: "en" },
    { label: "French", value: "fr" },
    { label: "German", value: "de" },
    { label: "Greek", value: "el" },
    { label: "Gujarati", value: "gu" },
    { label: "Hindi", value: "hi" },
    { label: "Italian", value: "it" },
    { label: "Japanese", value: "ja" },
    { label: "Korean", value: "ko" },
    { label: "Marathi", value: "mr" },
    { label: "Polish", value: "pl" },
    { label: "Portuguese", value: "pt" },
    { label: "Russian", value: "ru" },
    { label: "Spanish", value: "es" },
    { label: "Swedish", value: "sv" },
    { label: "Tamil", value: "ta" },
    { label: "Telugu", value: "te" },
    { label: "Thai", value: "th" },
    { label: "Turkish", value: "tr" },
    { label: "Urdu", value: "ur" },
  ];

  const captionOptions = [
    { label: "No Captions", value: "none" },
    { label: "Captions in Converted Language", value: "translated" },
    ...languageOptions
      .filter(lang => lang.value !== "zh")  
      .map(lang => ({
        label: `${lang.label}`,
        value: lang.value
      }))
  ];
  
  const handleFileChange = (event) => {
    setVideoFile(event.target.files[0]);
    setYoutubeUrl("");
    setUploadType("file");
    setErrorMessage("");
  };

  const handleYoutubeUrlChange = (event) => {
    setYoutubeUrl(event.target.value);
    setVideoFile(null);
    setUploadType("youtube");
    setErrorMessage("");
  };

  const handleUpload = async () => {
    if ((!videoFile && !youtubeUrl) || !language) {
      setErrorMessage(
        !videoFile && !youtubeUrl
          ? "Please upload a video file or provide a YouTube URL."
          : "Please select a language."
      );
      return;
    }

    const formData = new FormData();
    if (uploadType === "file") {
      formData.append("video", videoFile);
    } else {
      formData.append("youtube_url", youtubeUrl);
    }
    formData.append("language", language);
    formData.append("caption_option", captionOption);

    try {
      setLoading(true);
      setErrorMessage("");
      const response = await fetch("http://127.0.0.1:5000/upload", {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      if (data.error) {
        setErrorMessage(data.error);
        return;
      }
      
      const videoUrl = `http://127.0.0.1:5000/output_videos/${data.output_video}`;
      setTranslatedVideo(videoUrl);
      setVideoSummary(data.summary);
      setTranscription(data.transcription);
    } catch (error) {
      setErrorMessage("Failed to process the video. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-indigo-900">
      {/* Navigation */}
      <nav className="bg-black/20 backdrop-blur-sm fixed w-full z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-2xl text-white font-bold">Speech Translation</h1>
          <div className="space-x-6">
            <button className="text-gray-200 hover:text-white">
              Home
            </button>
            <button 
              onClick={() => scrollToSection(featuresRef)}
              className="text-gray-200 hover:text-white"
            >
              Features
            </button>
            <button 
              onClick={() => scrollToSection(howItWorksRef)}
              className="text-gray-200 hover:text-white"
            >
              How It Works
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-16">
        {/* Hero Section */}
        <div className="text-center py-20 px-4">
          <h1 className="text-6xl font-bold text-white mb-6">
            Transform Your Videos Into Any Language
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            Upload your video or paste a YouTube URL and get instant translations with perfect meaning and natural voices
          </p>
          
          {/* Main Upload Section */}
          <div className="max-w-4xl mx-auto bg-white/10 backdrop-blur-md rounded-xl p-8 shadow-2xl">
            <div className="grid gap-8">
              {/* Upload Type Selection */}
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => setUploadType("file")}
                  className={`px-6 py-2 rounded-lg transition-all ${
                    uploadType === "file"
                      ? "bg-blue-600 text-white"
                      : "bg-white/20 text-gray-300"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Upload size={20} />
                    Upload File
                  </span>
                </button>
                <button
                  onClick={() => setUploadType("youtube")}
                  className={`px-6 py-2 rounded-lg transition-all ${
                    uploadType === "youtube"
                      ? "bg-blue-600 text-white"
                      : "bg-white/20 text-gray-300"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Youtube size={20} />
                    YouTube URL
                  </span>
                </button>
              </div>

              {/* File Upload or YouTube URL Input */}
              <div>
                {uploadType === "file" ? (
                  <>
                    <label className="block text-white text-lg font-medium mb-4">Upload Video</label>
                    <input
                      type="file"
                      accept="video/mp4,video/mov"
                      onChange={handleFileChange}
                      className="w-full px-4 py-3 bg-white/20 border border-gray-300/30 rounded-lg text-white"
                    />
                  </>
                ) : (
                  <>
                    <label className="block text-white text-lg font-medium mb-4">
                      YouTube URL (max 1 minute)
                    </label>
                    <input
                      type="text"
                      value={youtubeUrl}
                      onChange={handleYoutubeUrlChange}
                      placeholder="https://www.youtube.com/watch?v=..."
                      className="w-full px-4 py-3 bg-white/20 border border-gray-300/30 rounded-lg text-white"
                    />
                  </>
                )}
              </div>

              {/* Language Selection */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-white text-lg font-medium mb-4">Target Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-3 bg-white/20 border border-gray-300/30 rounded-lg text-white"
                  >
                    {languageOptions.map((option) => (
                      <option key={option.value} value={option.value} className="text-black">
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-white text-lg font-medium mb-4">Caption Options</label>
                  <select
                    value={captionOption}
                    onChange={(e) => setCaptionOption(e.target.value)}
                    className="w-full px-4 py-3 bg-white/20 border border-gray-300/30 rounded-lg text-white"
                  >
                    {captionOptions.map((option) => (
                      <option key={option.value} value={option.value} className="text-black">
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Convert Button */}
              <button
                onClick={handleUpload}
                disabled={loading}
                className={`w-full py-4 rounded-lg text-white font-semibold text-lg transition-all ${
                  loading
                    ? "bg-blue-400/50 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-2"></div>
                    Processing...
                  </div>
                ) : (
                  "Start Translation"
                )}
              </button>

              {errorMessage && (
                <div className="text-red-400 text-sm font-medium">{errorMessage}</div>
              )}
            </div>
          </div>

          {/* Results Section */}
          {(videoFile || youtubeUrl || translatedVideo || videoSummary || transcription) && (
            <div className="max-w-4xl mx-auto mt-12 space-y-8">
              {/* Video Players */}
              <div className="grid grid-cols-2 gap-6">
  {/* Show original video if uploaded from file */}
  {videoFile && uploadType === "file" && (
    <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
      <h3 className="text-white font-medium mb-4">Original Video</h3>
      <video 
        src={URL.createObjectURL(videoFile)} 
        controls 
        className="w-full"
      />
    </div>
  )}

  {/* Show original video if uploaded from YouTube */}
  {youtubeUrl && uploadType === "youtube" && (
    <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
      <h3 className="text-white font-medium mb-4">Original Video</h3>
      <iframe 
        width="100%" 
        height="315" 
        src={`https://www.youtube.com/embed/${youtubeUrl.split("v=")[1].split("&")[0]}`} 
        title="YouTube Video"
        frameBorder="0"
        allowFullScreen
      ></iframe>
    </div>
  )}

  {/* Show translated video */}
  {translatedVideo && (
    <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
      <h3 className="text-white font-medium mb-4">Translated Video</h3>
      <video 
        src={translatedVideo} 
        controls 
        className="w-full"
      />
    </div>
  )}
</div>

              {/* Summary and Transcription */}
              {(videoSummary || transcription) && (
                <div className="grid grid-cols-2 gap-6">
                  {videoSummary && (
                    <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
                      <h2 className="text-white font-medium text-2xl mb-4">Video Summary</h2>
                      <p className="text-gray-300">{videoSummary}</p>
                    </div>
                  )}
                  
                  {transcription && (
                    <div className="bg-white/10 backdrop-blur-md rounded-xl p-6">
                      <h3 className="text-white font-medium mb-4 text-2xl">Transcription</h3>
                      <p className="text-gray-300">{transcription}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Features Section */}
        <div ref={featuresRef} className="py-20 px-4 bg-black/20">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold text-white text-center mb-12">Features</h2>
            <div className="grid grid-cols-3 gap-6">
              <Feature
                icon={<Globe size={24} />}
                title="Multi-Language"
                description="Support for 20+ languages with natural voice synthesis"
              />
              <Feature
                icon={<MessageSquare size={24} />}
                title="Smart Captions"
                description="Automatic caption generation and translation"
              />
              <Feature
                icon={<Zap size={24} />}
                title="Fast Processing"
                description="Quick translation with AI-powered technology"
              />
            </div>
          </div>
        </div>

        {/* How It Works Section */}
        <div ref={howItWorksRef} className="py-20 px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold text-white text-center mb-12">How It Works</h2>
            <div className="grid grid-cols-3 gap-6">
              <Step
                icon={uploadType === "youtube" ? <Youtube size={24} /> : <Upload size={24} />}
                title={uploadType === "youtube" ? "Add YouTube URL" : "Upload Video"}
                description={uploadType === "youtube" ? "Paste a YouTube video URL (max 1 min)" : "Upload your video file in MP4 or MOV format"}
                step={1}
              />
              <Step
                icon={<Settings size={24} />}
                title="Choose Settings"
                description="Select your target language and caption preferences"
                step={2}
              />
              <Step
                icon={<Play size={24} />}
                title="Get Results"
                description="Receive your translated video with natural voice and captions"
                step={3}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
// Feature Component
const Feature = ({ icon, title, description }) => (
  <div className="text-center p-6 bg-white/5 rounded-xl">
    <div className="inline-block p-3 bg-white/10 rounded-lg text-white mb-4">
      {icon}
    </div>
    <h3 className="text-white font-medium mb-2">{title}</h3>
    <p className="text-gray-400 text-sm">{description}</p>
  </div>
);

// Step Component
const Step = ({ icon, title, description, step }) => (
  <div className="text-center p-6 bg-white/5 rounded-xl relative">
    <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
      {step}
    </div>
    <div className="inline-block p-3 bg-white/10 rounded-lg text-white mb-4">
      {icon}
    </div>
    <h3 className="text-white font-medium mb-2">{title}</h3>
    <p className="text-gray-400 text-sm">{description}</p>
  </div>
);

export default App;