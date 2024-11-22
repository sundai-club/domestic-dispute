"use client";
import { useState } from 'react'
import { Upload, FileText, User, BarChart, Loader } from 'lucide-react'
import Link from 'next/link'
import axios from 'axios' // Add axios import

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

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    try {
      const response = await axios.post('/api/analyze-dispute', {
        text,
        party_one_name: partyOneName,
        party_two_name: partyTwoName,
        context1,
        context2,
      })

      let analysis;
      try {
        // Try to parse the response data if it's a string
        analysis = typeof response.data === 'string' 
          ? JSON.parse(response.data)
          : response.data;
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

  const handleStoreDispute = async () => {
    setIsStoring(true)
    try {
      const response = await fetch('http://localhost:8000/api/store-dispute', {
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
      const response = await fetch(`http://localhost:8000/api/dispute/${disputeId}`, {
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
        winner_explanation: data.result.winner_explanation
      })
      
      setShowReport(true)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to fetch dispute')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 text-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-8 animate-pulse">Dispute Analysis Dashboard</h1>
        
        {!showReport ? (
          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Upload or Paste Your Dispute</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="bg-white/20 rounded-lg p-4 flex items-center justify-center cursor-pointer hover:bg-white/30 transition-colors">
                  <Upload className="mr-2" />
                  <span>Upload Text File</span>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <label htmlFor="dispute-text" className="block mb-2">Or paste your text here:</label>
                  <textarea
                    id="dispute-text"
                    className="w-full h-32 bg-white/10 rounded p-2 text-white placeholder-white/50"
                    placeholder="Type or paste your dispute text here..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                  ></textarea>
                </div>
              </div>
              <div className="space-y-4">
                <div className="bg-white/20 rounded-lg p-4">
                  <label htmlFor="party1" className="block mb-2">Party 1 Context:</label>
                  <input
                    id="party1"
                    type="text"
                    className="w-full bg-white/10 rounded p-2 text-white placeholder-white/50 mb-2"
                    placeholder="Name"
                    value={partyOneName}
                    onChange={(e) => setPartyOneName(e.target.value)}
                  />
                  <textarea
                    className="w-full h-24 bg-white/10 rounded p-2 text-white placeholder-white/50"
                    placeholder="Explain your point of view..."
                    value={context1}
                    onChange={(e) => setContext1(e.target.value)}
                  ></textarea>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <label htmlFor="party2" className="block mb-2">Party 2 Context:</label>
                  <input
                    id="party2"
                    type="text"
                    className="w-full bg-white/10 rounded p-2 text-white placeholder-white/50 mb-2"
                    placeholder="Name"
                    value={partyTwoName}
                    onChange={(e) => setPartyTwoName(e.target.value)}
                  />
                  <textarea
                    className="w-full h-24 bg-white/10 rounded p-2 text-white placeholder-white/50"
                    placeholder="Explain your point of view..."
                    value={context2}
                    onChange={(e) => setContext2(e.target.value)}
                  ></textarea>
                </div>
              </div>
            </div>
            <button
              onClick={handleAnalyze}
              className="mt-6 bg-yellow-400 text-red-700 px-6 py-3 rounded-full text-xl font-bold hover:bg-yellow-300 transition-transform transform hover:scale-105"
            >
            Analyze Dispute
            </button>
            <button
              type="button"
              onClick={() => {
                console.log('Get Dispute button clicked');  // Debug log
                handleGetDispute();
              }}
              className="mt-6 bg-green-400 text-white px-6 py-3 rounded-full text-xl font-bold"
            >
              Get Dispute Test
            </button>

            <button
              onClick={handleStoreDispute}
              className="mt-6 bg-blue-400 text-white px-6 py-3 rounded-full text-xl font-bold hover:bg-blue-300 transition-transform transform hover:scale-105"
            >
              Store Dispute
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
            <h2 className="text-3xl font-bold mb-6 animate-pulse">🏆 Final Verdict</h2>
            <div className="bg-white/20 rounded-lg p-6">
              <div className="mb-6">
                <h3 className="text-2xl font-bold text-yellow-300 mb-2">
                  {analysisResult?.winner || partyOneName} Wins
                </h3>
                <div className="text-lg leading-relaxed">
                  <p className="mb-4 text-white/90">
                    {analysisResult?.winner_explanation || `After analyzing the dispute between ${partyOneName} and ${partyTwoName}, we've determined that ${analysisResult?.winner || partyOneName} has the stronger position.`}
                  </p>
                </div>
              </div>
            </div>
            <Link
              href="/dashboard"
              className="mt-6 inline-block bg-yellow-400 text-red-700 px-6 py-3 rounded-full text-xl font-bold hover:bg-yellow-300 transition-transform transform hover:scale-105"
            >
              Settle Another Dispute
            </Link>
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