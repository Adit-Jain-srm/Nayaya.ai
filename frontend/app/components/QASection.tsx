'use client'

import { useState } from 'react'
import { QAResponse } from '../types'
import { PaperAirplaneIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'
import axios from 'axios'

interface QASectionProps {
  documentId: string
}

export default function QASection({ documentId }: QASectionProps) {
  const [question, setQuestion] = useState('')
  const [qaHistory, setQaHistory] = useState<QAResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const suggestedQuestions = [
    "What happens if I miss a payment?",
    "Can I terminate this contract early?",
    "What are my data privacy rights?",
    "Who is responsible for maintenance and repairs?",
    "Can the terms be changed after signing?",
    "What fees might I be charged?",
    "What happens in case of a dispute?"
  ]

  const handleSubmitQuestion = async (questionText: string) => {
    if (!questionText.trim()) return

    setIsLoading(true)
    setQuestion('')

    try {
      // Mock API call - replace with actual API
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/qa`, {
        documentId,
        question: questionText
      })

      // Mock response for development
      const mockResponse: QAResponse = {
        question: questionText,
        answer: generateMockAnswer(questionText),
        confidence: 0.85,
        sources: ['Clause 3.2 - Payment Terms', 'Clause 7.1 - Termination']
      }

      setQaHistory(prev => [...prev, mockResponse])
    } catch (error) {
      console.error('QA failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const generateMockAnswer = (question: string): string => {
    if (question.toLowerCase().includes('payment')) {
      return "If you miss a payment, you'll be charged a late fee of $50 and given 5 days to cure the default. After 5 days, the landlord can begin eviction proceedings. However, this may vary based on local tenant protection laws."
    }
    if (question.toLowerCase().includes('terminate') || question.toLowerCase().includes('early')) {
      return "You can terminate the contract early by giving 60 days written notice and paying an early termination fee equal to 2 months' rent. This fee is quite high and you may want to negotiate this term."
    }
    return "Based on the contract terms, this would depend on the specific clauses related to your question. I recommend reviewing the relevant sections and consulting with a legal professional for specific guidance."
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Question Input */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <ChatBubbleLeftRightIcon className="h-6 w-6 mr-2 text-primary-600" />
          Ask Questions About Your Document
        </h2>
        
        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmitQuestion(question)}
              placeholder="Ask anything about your contract..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={() => handleSubmitQuestion(question)}
            disabled={isLoading || !question.trim()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
            <span>Ask</span>
          </button>
        </div>

        {/* Suggested Questions */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Suggested Questions:</h3>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((suggested, index) => (
              <button
                key={index}
                onClick={() => handleSubmitQuestion(suggested)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                disabled={isLoading}
              >
                {suggested}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* QA History */}
      {qaHistory.length > 0 && (
        <div className="space-y-4">
          {qaHistory.map((qa, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border overflow-hidden">
              {/* Question */}
              <div className="bg-primary-50 px-6 py-4 border-b">
                <p className="font-medium text-gray-900">{qa.question}</p>
              </div>
              
              {/* Answer */}
              <div className="px-6 py-4">
                <p className="text-gray-700 leading-relaxed mb-4">{qa.answer}</p>
                
                {/* Sources & Confidence */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center space-x-4">
                    <span>Confidence: {Math.round(qa.confidence * 100)}%</span>
                    {qa.sources.length > 0 && (
                      <div className="flex items-center space-x-2">
                        <span>Sources:</span>
                        <div className="flex space-x-2">
                          {qa.sources.map((source, i) => (
                            <span key={i} className="px-2 py-1 bg-gray-100 rounded text-xs">
                              {source}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
            <span className="text-gray-600">Analyzing your question...</span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {qaHistory.length === 0 && !isLoading && (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <ChatBubbleLeftRightIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No questions yet</h3>
          <p className="text-gray-600">Ask any question about your contract to get started.</p>
        </div>
      )}
    </div>
  )
}
