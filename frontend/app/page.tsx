'use client'

import { useState } from 'react'
import DocumentUpload from './components/DocumentUpload'
import DocumentAnalysis from './components/DocumentAnalysis'
import { DocumentAnalysisResult } from './types'

export default function Home() {
  const [analysisResult, setAnalysisResult] = useState<DocumentAnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleAnalysisComplete = (result: DocumentAnalysisResult) => {
    setAnalysisResult(result)
    setIsAnalyzing(false)
  }

  const handleNewDocument = () => {
    setAnalysisResult(null)
    setIsAnalyzing(false)
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        {!analysisResult && !isAnalyzing && (
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Simplify Complex Legal Documents
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Upload your rental agreement, loan contract, or terms of service. 
              Get plain-language explanations, risk assessments, and answers to your questions.
            </p>
          </div>
        )}

        {!analysisResult ? (
          <DocumentUpload 
            onAnalysisStart={() => setIsAnalyzing(true)}
            onAnalysisComplete={handleAnalysisComplete}
            isAnalyzing={isAnalyzing}
          />
        ) : (
          <DocumentAnalysis 
            result={analysisResult}
            onNewDocument={handleNewDocument}
          />
        )}
      </div>
    </main>
  )
}
