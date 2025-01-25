import React, { useState } from "react";
import axios from "axios";
import ReactPlayer from "react-player";
import image from "./images/background.png";

function App() {
  const [videoFile, setVideoFile] = useState(null);
  const [language, setLanguage] = useState("en");
  const [captionOption, setCaptionOption] = useState("none");
  const [translatedVideo, setTranslatedVideo] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const languageOptions = [
    { label: "Arabic", value: "ar" },
    { label: "Bengali", value: "bn" },
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
    { label: "Malayalam", value: "ml" },
    { label: "Marathi", value: "mr" },
    { label: "Persian", value: "fa" },
    { label: "Polish", value: "pl" },
    { label: "Portuguese", value: "pt" },
    { label: "Punjabi", value: "pa" },
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
  ...languageOptions.map(lang => ({
    label: `${lang.label}`, 
    value: lang.value 
  }))
];
<select name="captions" id="captions">
  {captionOptions.map(option => (
    <option value={option.value} key={option.value}>
      {option.label}
    </option>
  ))}
</select>

  const handleFileChange = (event) => {
    setVideoFile(event.target.files[0]);
    setErrorMessage("");
  };

  const handleUpload = async () => {
    if (!videoFile || !language) {
      setErrorMessage(
        !videoFile
          ? "Please upload a video file."
          : "Please select a language."
      );
      return;
    }

    const formData = new FormData();
    formData.append("video", videoFile);
    formData.append("language", language);
    formData.append("caption_option", captionOption);  

    try {
      setLoading(true);
      setErrorMessage("");
      const response = await axios.post("http://127.0.0.1:5000/upload", formData);
      const videoUrl = `http://127.0.0.1:5000/output_videos/${response.data.output_video}`;
      setTranslatedVideo(videoUrl);
    } catch (error) {
      setErrorMessage("Failed to process the video. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex bg-gradient-to-r from-blue-50 to-blue-100 justify-center h-28">
        <h1 className="text-8xl bg-gradient-to-r from-blue-400 to-blue-900 bg-clip-text text-transparent animate-flow">
          Speech To Speech Streaming
        </h1>
      </div>
      <div className="relative bg-gradient-to-r from-blue-50 to-blue-100 min-h-screen flex flex-col items-center justify-start px-4">
        <div className="absolute inset-0 z-0">
          <img
            src={image}
            alt="Background"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="z-20 bg-blue-50 shadow-lg rounded-lg p-6 w-full max-w-3xl mt-12">
          <div className="flex justify-between">
            <h1 className="text-2xl py-2">Upload Your Video</h1>
            <p className="text-xs mt-4 text-gray-500">Only MP4 and MOV formats</p>
          </div>
          <input
            type="file"
            accept="video/mp4, video/mov"
            onChange={handleFileChange}
            className="block w-full text-base text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring focus:ring-blue-300"
          />
          <h1 className="text-2xl py-2">Choose Language</h1>
          <div className="mb-4 relative">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="block w-full px-3 py-2 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring focus:ring-blue-300 appearance-none"
            >
              {languageOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none">
              &#9660;
            </span>
          </div>

          <h1 className="text-2xl pr-2">Choose Captions</h1>
          <div className="mb-4 relative">
            <select
              value={captionOption}
              onChange={(e) => setCaptionOption(e.target.value)}
              className="block w-full px-3 py-2 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring focus:ring-blue-300 appearance-none"
            >
              {captionOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none">
              &#9660;
            </span>
          </div>

          {errorMessage && (
            <div className="text-red-500 text-sm font-medium mb-4">
              {errorMessage}
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={loading}
            className={`w-full px-4 py-2 text-white font-semibold rounded-lg ${
              loading
                ? "bg-blue-300 cursor-not-allowed"
                : "bg-blue-500 hover:bg-blue-600"
            }`}
          >
            {loading ? "Processing..." : "Convert Video"}
          </button>

          {loading && (
            <div className="flex justify-center items-center mt-6">
              <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500"></div>
              <p className="text-gray-600 text-lg ml-4">Almost there...</p>
            </div>
          )}

          <div className="mt-6">
            {videoFile && (
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-2">
                  Original Video
                </h2>
                <ReactPlayer url={URL.createObjectURL(videoFile)} controls />
              </div>
            )}

            {translatedVideo && (
              <div>
                <h2 className="text-lg font-semibold text-gray-800 mb-2">
                  Translated Video
                </h2>
                <ReactPlayer url={translatedVideo} controls />
                <p className="text-xs mt-4 text-gray-500">
                  To download your translated video, click on 3 dots and download
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
