"use client";
import axios from 'axios'; // Add axios import
import { Upload } from 'lucide-react';
import { useState } from 'react';

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(false)
  const [showReport, setShowReport] = useState(false)
  const [text, setText] = useState('')
  const [partyOneName, setPartyOneName] = useState('')
  const [partyTwoName, setPartyTwoName] = useState('')
  const [context1, setContext1] = useState('')
  const [context2, setContext2] = useState('')
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [disputeId, setDisputeId] = useState<number | null>(null)
  const [disputeResult, setDisputeResult] = useState<any>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isStoring, setIsStoring] = useState(false)

  const STAGE = process.env.stage === undefined ? 'prod' : 'dev'; 
  console.log("stage: " + STAGE)

  const BACKEND_URL =
    STAGE === 'prod'
      ? "https://domestic-dispute-199983032721.us-central1.run.app"
      : "http://localhost:8000";

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    try {
      const response = await axios.post(`${BACKEND_URL}/api/analyze-dispute`, {
        name1: partyOneName,
        name2: partyTwoName,
        conversation: text,
      })

      // Log the raw response
      console.log('Raw response:', response)
      console.log('Response data:', response.data)

      let analysis;
      try {
        // Try to parse the response data if it's a string
        analysis = typeof response.data === 'string' 
          ? JSON.parse(response.data)
          : response.data;

      console.log("analysis"+ analysis)
      } catch (parseError) {
        // If parsing fails, create a basic response
        analysis = {
          winner: partyOneName,
          winner_explanation: "Based on the available information, we'll give this one to " + partyOneName
        };
      }

      setAnalysisResult(analysis)
      setShowReport(true)
    } catch (error) {
      console.error(error)
      // Set a fallback result if the request fails
      setAnalysisResult({
        winner: partyOneName,
        winner_explanation: "Due to technical difficulties, we're defaulting to " + partyOneName
      })
      setShowReport(true)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();

    // Append all selected files
    Array.from(files).forEach((file) => {
      if (file.size > 5000000) {
        alert(`File "${file.name}" is too large. Please upload files smaller than 5MB.`);
        return;
      }
      formData.append('files', file);
    });

    setIsLoading(true); // Show loading screen

    try {
      // Call the API
      const response = await axios.post(`${BACKEND_URL}/api/upload-image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { conversation } = response.data;

      // Update the text area with the conversation text
      setText(conversation || ''); // Set conversation text
    } catch (error) {
      console.error('Error uploading files:', error);
      alert('Failed to process the files. Please try again.');
    } finally {
      setIsLoading(false); // Hide loading screen
    }
  };

  const handleStoreDispute = async () => {
    setIsStoring(true)
    try {
      const response = await fetch(`${BACKEND_URL}/api/store-dispute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          party_one_name: partyOneName,
          party_two_name: partyTwoName,
          context1: context1,
          context2: context2,
          text: text,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()

      if (data.dispute_id) {
        setDisputeId(data.dispute_id)
        /*alert(`Dispute stored successfully with ID: ${data.dispute_id}`)*/
      } else {
        throw new Error('No dispute ID received in response')
      }
    } catch (error) {
      console.error('Error storing dispute:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      alert(`Failed to store dispute: ${errorMessage}`)
    } finally {
      setIsStoring(false)
    }
  }

  const handleGetDispute = async () => {
    console.log('Starting getDispute with ID:', disputeId);
    if (!disputeId) {
      alert('No dispute ID available');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/dispute/${disputeId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const data = await response.json()
      
      // Set form data
      setPartyOneName(data.party_one_name)
      setPartyTwoName(data.party_two_name)
      setContext1(data.context1)
      setContext2(data.context2)
      setText(data.conversation)

      // Set analysis result
      setAnalysisResult({
        winner: data.result.winner,
        winner_explanation: data.result.winner.explanation
      })
      
      setShowReport(true)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to fetch dispute')
    }
  }

  const handleReset = () => {
    // Reset all form states
    setText('');
    setPartyOneName('');
    setPartyTwoName('');
    setContext1('');
    setContext2('');
    setAnalysisResult(null);
    setDisputeId(null);
    setDisputeResult(null);
    // Hide the report view
    setShowReport(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 text-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8 animate-pulse">Dispute Analysis Dashboard</h1>

        {/* Loading Screen for File Upload */}
        {isLoading && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 text-center">
              <div className="animate-spin-slow rounded-full h-32 w-32 border-t-4 border-b-4 border-blue-500 mx-auto mb-4"></div>
              <p className="text-xl font-semibold text-blue-500">Uploading your files...</p>
              <p className="text-gray-600">Please wait while we process your images.</p>
            </div>
          </div>
        )}
        
        {!showReport ? (
          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-8">
            <h2 className="text-5xl font-semibold mb-4">Upload or Paste Your Dispute</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="bg-white/20 rounded-lg p-4 space-y-2">
                  <label htmlFor="dispute-text" className="text-2xl block mb-2 flex items-center justify-center">
                    Dispute Text
                  </label>
                  {/* Conversation Text */}
                  <textarea
                    id="conversation-text"
                    className="text-lg w-full h-32 bg-white/10 rounded p-2 text-white placeholder-white/50"
                    placeholder="Paste text or upload screenshots..."
                    value={text}
                    onChange={(e) => setText(e.target.value)} // Update state as user edits or deletes
                  ></textarea>

                  {/* File Upload */}
                  <div className="relative ">
                    <input
                      type="file"
                      accept=".jpg,.jpeg,.png"
                      multiple
                      onChange={handleFileUpload}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <div className="text-xl bg-white/20 rounded-lg p-4 flex items-center justify-center hover:bg-white/30 transition-colors">
                      <Upload className="mr-2" />
                      <span>Upload Screenshots</span>
                    </div>
                </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="bg-white/20 rounded-lg p-4">
                  <label htmlFor="party1" className="text-2xl block mb-2 flex items-center justify-center">Party 1</label>
                  <input
                    id="party1"
                    type="text"
                    className="text-lg w-full bg-white/10 rounded p-2 text-white placeholder-white/50 mb-2"
                    placeholder="Name"
                    value={partyOneName}
                    onChange={(e) => setPartyOneName(e.target.value)}
                  />
                  {/*<textarea
                    className="w-full h-24 bg-white/10 rounded p-2 text-white placeholder-white/50"
                    placeholder="Explain your point of view..."
                    value={context1}
                    onChange={(e) => setContext1(e.target.value)}
                  ></textarea>*/}
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <label htmlFor="party2" className="text-2xl block mb-2 flex items-center justify-center">Party 2</label>
                  <input
                    id="party2"
                    type="text"
                    className="text-lg w-full bg-white/10 rounded p-2 text-white placeholder-white/50 mb-2"
                    placeholder="Name"
                    value={partyTwoName}
                    onChange={(e) => setPartyTwoName(e.target.value)}
                  />
                  {/*<textarea
                    className="w-full h-24 bg-white/10 rounded p-2 text-white placeholder-white/50"
                    placeholder="Explain your point of view..."
                    value={context2}
                    onChange={(e) => setContext2(e.target.value)}
                  ></textarea>*/}
                </div>
              </div>
            </div>
            <button
              onClick={handleAnalyze}
              className="mt-6 bg-yellow-400 text-red-700 px-6 py-3 rounded-full text-xl font-bold hover:bg-yellow-300 transition-transform transform hover:scale-105"
            >
            Analyze Dispute
            </button>
            {/*
            <button
              onClick={() => {
                console.log('Get Dispute button clicked');  // Debug log
                handleGetDispute();
              }}
              className="mt-6 bg-green-400 text-white px-6 py-3 rounded-full text-xl font-bold hover:bg-green-300 transition-transform transform hover:scale-105"
            >
              Get Dispute
            </button>*/}
          </div>
        ) : (
          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-8">
            <h2 className="text-5xl font-bold mb-6 animate-pulse">🏆 Final Verdict 🏆</h2>
            <div className="bg-white/20 rounded-lg p-6 mb-4">
              <div className="mb-6">
                <div className="flex justify-center items-center">
                  <h3 className="text-4xl font-bold text-white-300 mb-2">
                    {analysisResult?.winner?.name || partyOneName} is declared the winner!
                  </h3>
                </div>
              </div>
            </div>


              
            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              
              {/* Left Column */}
              <div className="space-y-4">
                <div className="bg-white/20 rounded-lg p-4">
                  <h3 className="text-4xl flex justify-center font-bold text-white-300 mb-4"> 👑 {analysisResult?.winner?.name} 👑</h3>
                  <div className="space-y-3">
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl"><span className="font-bold">Winner Explanation:</span> {analysisResult?.winner?.explanation}</p>
                    </div>
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl"><span className="font-bold">Logical Score:</span> {analysisResult?.winner?.logical_score}</p>
                    </div>
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl"><span className="font-bold">Tonality:</span> {analysisResult?.winner?.tonality}</p>
                    </div>
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl mb-2">
                        <span className="font-bold">Volume:</span> {Math.round(analysisResult?.winner?.volume_percentage)}%
                      </p>
                      <div className="w-full bg-gray-700 rounded-full h-2.5">
                        <div 
                          className="bg-blue-300 h-2.5 rounded-full transition-all duration-500" 
                          style={{ width: `${analysisResult?.winner?.volume_percentage}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    {/* Winner's Personal Attacks */}
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl font-semibold mb-2">
                        {analysisResult?.winner?.personal_attacks?.length > 0 
                          ? "Top Personal Attacks:"
                          : "No Personal Attacks 💖"}
                      </p>
                      {analysisResult?.winner?.personal_attacks?.length > 0 && (
                        <ul className="list-disc pl-4 space-y-2">
                          {analysisResult.winner.personal_attacks.slice(0, 4).map((attack: string, index: number) => (
                            <li key={index} className="text-xl">{attack}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                <div className="bg-white/20 rounded-lg p-4">
                  <h3 className="text-4xl flex justify-center font-bold text-white-300 mb-4"> 🛋️ {analysisResult?.loser?.name} 🛋️</h3>
                  <div className="space-y-3">
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl"><span className="font-bold">Loser Explanation:</span> {analysisResult?.loser?.explanation}</p>
                    </div>
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl"><span className="font-bold">Logical Score:</span> {analysisResult?.loser?.logical_score}</p>
                    </div>
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl"><span className="font-bold">Tonality:</span> {analysisResult?.loser?.tonality}</p>
                    </div>
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl mb-2">
                        <span className="font-bold">Volume:</span> {Math.round(analysisResult?.loser?.volume_percentage)}%
                      </p>
                      <div className="w-full bg-gray-700 rounded-full h-2.5">
                        <div 
                          className="bg-blue-300 h-2.5 rounded-full transition-all duration-500" 
                          style={{ width: `${analysisResult?.loser?.volume_percentage}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Loser's Personal Attacks */}
                    <div className="bg-white/10 rounded p-2">
                      <p className="text-xl font-semibold mb-2">
                        {analysisResult?.loser?.personal_attacks?.length > 0 
                          ? "Top Personal Attacks:"
                          : "No Personal Attacks 💖"}
                      </p>
                      {analysisResult?.loser?.personal_attacks?.length > 0 && (
                        <ul className="list-disc pl-4 space-y-2">
                          {analysisResult.loser.personal_attacks.slice(0, 4).map((attack: string, index: number) => (
                            <li key={index} className="text-xl">{attack}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Full JSON Output */}
            {/*<div className="text-lg leading-relaxed">
              <pre className="mb-4 text-white/90 whitespace-pre-wrap">
                {JSON.stringify(analysisResult, null, 2)}
              </pre>
            </div>*/}

            <button
              onClick={handleReset}
              className="mt-6 inline-block bg-yellow-400 text-red-700 px-6 py-3 rounded-full text-xl font-bold hover:bg-yellow-300 transition-transform transform hover:scale-105"
            >
              Settle Another Dispute
            </button>
          </div>
        )}

        {isAnalyzing && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 text-center">
              <div className="animate-spin-slow rounded-full h-32 w-32 border-t-4 border-b-4 border-red-500 mx-auto mb-4"></div>
              <p className="text-xl font-semibold text-red-500">Analyzing your dispute...</p>
              <p className="text-gray-600">Please wait while our AI settles your argument.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}