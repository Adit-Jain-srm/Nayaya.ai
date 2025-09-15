'use client'

import { useState } from 'react'
import { DocumentAnalysisResult, QAResponse } from '../types'
import ClauseCard from './ClauseCard'
import QASection from './QASection'
import ExportReport from './ExportReport'
import { 
  DocumentTextIcon, 
  ExclamationTriangleIcon, 
  CheckCircleIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'

interface DocumentAnalysisProps {
  result: DocumentAnalysisResult
  onNewDocument: () => void
}

export default function DocumentAnalysis({ result, onNewDocument }: DocumentAnalysisProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'clauses' | 'qa' | 'export'>('overview')

  const riskColors = {
    high: 'text-red-600 bg-red-100',
    medium: 'text-yellow-600 bg-yellow-100',
    low: 'text-green-600 bg-green-100'
  }

  const riskIcons = {
    high: ExclamationTriangleIcon,
    medium: ExclamationTriangleIcon,
    low: CheckCircleIcon
  }

  const RiskIcon = riskIcons[result.overallRisk]

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border mb-6 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onNewDocument}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{result.fileName}</h1>
              <p className="text-gray-600">{result.documentType} • Analyzed {new Date(result.processedAt).toLocaleString()}</p>
            </div>
          </div>
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${riskColors[result.overallRisk]}`}>
            <RiskIcon className="h-5 w-5" />
            <span className="font-semibold capitalize">{result.overallRisk} Risk</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm border mb-6">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {[
            { key: 'overview', label: 'Overview', icon: DocumentTextIcon },
            { key: 'clauses', label: `Clauses (${result.clauses.length})`, icon: DocumentTextIcon },
            { key: 'qa', label: 'Ask Questions', icon: DocumentTextIcon },
            { key: 'export', label: 'Export Report', icon: DocumentTextIcon }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`
                flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab.key
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Summary */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Document Summary</h2>
                <p className="text-gray-700 leading-relaxed">{result.summary}</p>
              </div>
            </div>

            {/* Key Findings */}
            <div>
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Findings</h2>
                <ul className="space-y-3">
                  {result.keyFindings.map((finding, index) => (
                    <li key={index} className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                      <span className="text-gray-700 text-sm">{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Risk Distribution */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Distribution</h2>
                <div className="grid grid-cols-3 gap-4">
                  {(['high', 'medium', 'low'] as const).map((risk) => {
                    const count = result.clauses.filter(c => c.riskLevel === risk).length
                    return (
                      <div key={risk} className="text-center">
                        <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center ${riskColors[risk]}`}>
                          <span className="text-2xl font-bold">{count}</span>
                        </div>
                        <p className="text-sm font-medium text-gray-900 capitalize">{risk} Risk</p>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'clauses' && (
          <div className="space-y-6">
            {result.clauses.map((clause) => (
              <ClauseCard key={clause.id} clause={clause} />
            ))}
          </div>
        )}

        {activeTab === 'qa' && (
          <QASection documentId={result.documentId} />
        )}

        {activeTab === 'export' && (
          <ExportReport result={result} />
        )}
      </div>
    </div>
  )
}
