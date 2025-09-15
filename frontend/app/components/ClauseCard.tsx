'use client'

import { useState } from 'react'
import { ClauseAnalysis } from '../types'
import { 
  ChevronDownIcon, 
  ChevronUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline'

interface ClauseCardProps {
  clause: ClauseAnalysis
}

export default function ClauseCard({ clause }: ClauseCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const riskColors = {
    high: 'border-red-300 bg-red-50',
    medium: 'border-yellow-300 bg-yellow-50',
    low: 'border-green-300 bg-green-50'
  }

  const riskTextColors = {
    high: 'text-red-700',
    medium: 'text-yellow-700',
    low: 'text-green-700'
  }

  const riskIcons = {
    high: ExclamationTriangleIcon,
    medium: ExclamationTriangleIcon,
    low: CheckCircleIcon
  }

  const RiskIcon = riskIcons[clause.riskLevel]

  return (
    <div className={`border-2 rounded-lg overflow-hidden ${riskColors[clause.riskLevel]}`}>
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{clause.type}</h3>
              <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${riskTextColors[clause.riskLevel]} bg-white`}>
                <RiskIcon className="h-4 w-4" />
                <span className="capitalize">{clause.riskLevel}</span>
              </div>
            </div>
            
            {/* Plain Language Summary */}
            <div className="bg-white rounded-lg p-4 mb-4">
              <h4 className="font-medium text-gray-900 mb-2">Plain Language</h4>
              <p className="text-gray-700">{clause.plainLanguage}</p>
            </div>

            {/* Risk Reason */}
            <div className="flex items-start space-x-2 mb-4">
              <ExclamationTriangleIcon className={`h-5 w-5 mt-0.5 ${riskTextColors[clause.riskLevel]}`} />
              <div>
                <h4 className="font-medium text-gray-900 mb-1">Why this matters</h4>
                <p className="text-gray-700 text-sm">{clause.riskReason}</p>
              </div>
            </div>

            {/* Recommendations */}
            {clause.recommendations.length > 0 && (
              <div className="flex items-start space-x-2">
                <LightBulbIcon className="h-5 w-5 mt-0.5 text-blue-600" />
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
                  <ul className="space-y-1">
                    {clause.recommendations.map((rec, index) => (
                      <li key={index} className="text-gray-700 text-sm flex items-start">
                        <span className="text-blue-600 mr-2">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="ml-4 p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-white"
          >
            {isExpanded ? (
              <ChevronUpIcon className="h-5 w-5" />
            ) : (
              <ChevronDownIcon className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-white p-6">
          <div className="space-y-4">
            {/* Original Text */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Original Contract Text</h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 text-sm font-mono leading-relaxed">
                  "{clause.originalText}"
                </p>
              </div>
            </div>

            {/* Citations */}
            {clause.citations && clause.citations.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Legal References</h4>
                <ul className="space-y-1">
                  {clause.citations.map((citation, index) => (
                    <li key={index} className="text-blue-600 text-sm hover:underline cursor-pointer">
                      {citation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
