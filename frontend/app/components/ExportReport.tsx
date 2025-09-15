'use client'

import { useState } from 'react'
import { DocumentAnalysisResult } from '../types'
import { DocumentArrowDownIcon, PrinterIcon } from '@heroicons/react/24/outline'
import jsPDF from 'jspdf'

interface ExportReportProps {
  result: DocumentAnalysisResult
}

export default function ExportReport({ result }: ExportReportProps) {
  const [isGenerating, setIsGenerating] = useState(false)

  const generatePDF = async () => {
    setIsGenerating(true)
    
    try {
      const pdf = new jsPDF()
      const pageWidth = pdf.internal.pageSize.getWidth()
      const margin = 20
      let yPosition = margin

      // Header
      pdf.setFontSize(20)
      pdf.text('Legal Document Analysis Report', margin, yPosition)
      yPosition += 15

      pdf.setFontSize(12)
      pdf.text(`Document: ${result.fileName}`, margin, yPosition)
      yPosition += 10
      pdf.text(`Type: ${result.documentType}`, margin, yPosition)
      yPosition += 10
      pdf.text(`Overall Risk: ${result.overallRisk.toUpperCase()}`, margin, yPosition)
      yPosition += 10
      pdf.text(`Analyzed: ${new Date(result.processedAt).toLocaleDateString()}`, margin, yPosition)
      yPosition += 20

      // Summary
      pdf.setFontSize(16)
      pdf.text('Executive Summary', margin, yPosition)
      yPosition += 10

      pdf.setFontSize(10)
      const summaryLines = pdf.splitTextToSize(result.summary, pageWidth - 2 * margin)
      pdf.text(summaryLines, margin, yPosition)
      yPosition += summaryLines.length * 5 + 15

      // Key Findings
      pdf.setFontSize(16)
      pdf.text('Key Findings', margin, yPosition)
      yPosition += 10

      pdf.setFontSize(10)
      result.keyFindings.forEach((finding, index) => {
        const findingText = `${index + 1}. ${finding}`
        const findingLines = pdf.splitTextToSize(findingText, pageWidth - 2 * margin)
        pdf.text(findingLines, margin, yPosition)
        yPosition += findingLines.length * 5 + 5
      })

      yPosition += 10

      // Risk Analysis
      pdf.setFontSize(16)
      pdf.text('Risk Analysis by Clause', margin, yPosition)
      yPosition += 15

      result.clauses.forEach((clause, index) => {
        // Check if we need a new page
        if (yPosition > pdf.internal.pageSize.getHeight() - 50) {
          pdf.addPage()
          yPosition = margin
        }

        pdf.setFontSize(12)
        pdf.text(`${index + 1}. ${clause.type} - ${clause.riskLevel.toUpperCase()} RISK`, margin, yPosition)
        yPosition += 10

        pdf.setFontSize(10)
        const plainLanguageLines = pdf.splitTextToSize(clause.plainLanguage, pageWidth - 2 * margin)
        pdf.text(plainLanguageLines, margin, yPosition)
        yPosition += plainLanguageLines.length * 5 + 5

        pdf.text(`Risk Reason: ${clause.riskReason}`, margin, yPosition)
        yPosition += 10

        if (clause.recommendations.length > 0) {
          pdf.text('Recommendations:', margin, yPosition)
          yPosition += 5
          clause.recommendations.forEach((rec) => {
            const recLines = pdf.splitTextToSize(`• ${rec}`, pageWidth - 2 * margin)
            pdf.text(recLines, margin + 5, yPosition)
            yPosition += recLines.length * 5
          })
        }
        yPosition += 10
      })

      // Disclaimer
      if (yPosition > pdf.internal.pageSize.getHeight() - 40) {
        pdf.addPage()
        yPosition = margin
      }

      pdf.setFontSize(14)
      pdf.text('Important Disclaimer', margin, yPosition)
      yPosition += 10

      pdf.setFontSize(10)
      const disclaimer = 'This analysis is provided for educational purposes only and does not constitute legal advice. Please consult with a qualified attorney for legal decisions.'
      const disclaimerLines = pdf.splitTextToSize(disclaimer, pageWidth - 2 * margin)
      pdf.text(disclaimerLines, margin, yPosition)

      // Save the PDF
      pdf.save(`${result.fileName}_analysis_report.pdf`)
    } catch (error) {
      console.error('PDF generation failed:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const printReport = () => {
    window.print()
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border p-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Export Analysis Report</h2>
          <p className="text-gray-600">
            Generate a comprehensive PDF report of your document analysis, 
            including risk assessments and recommendations.
          </p>
        </div>

        {/* Report Preview */}
        <div className="bg-gray-50 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Report Contents</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Document Overview</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Document metadata and type</li>
                <li>• Overall risk assessment</li>
                <li>• Executive summary</li>
                <li>• Key findings and concerns</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Detailed Analysis</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Clause-by-clause breakdown</li>
                <li>• Risk levels and explanations</li>
                <li>• Plain language translations</li>
                <li>• Actionable recommendations</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Export Options */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={generatePDF}
            disabled={isGenerating}
            className="flex items-center justify-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            <span>{isGenerating ? 'Generating PDF...' : 'Download PDF Report'}</span>
          </button>

          <button
            onClick={printReport}
            className="flex items-center justify-center space-x-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            <PrinterIcon className="h-5 w-5" />
            <span>Print Report</span>
          </button>
        </div>

        {/* Report Stats */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{result.clauses.length}</div>
            <div className="text-sm text-gray-600">Total Clauses</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {result.clauses.filter(c => c.riskLevel === 'high').length}
            </div>
            <div className="text-sm text-red-600">High Risk</div>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {result.clauses.filter(c => c.riskLevel === 'medium').length}
            </div>
            <div className="text-sm text-yellow-600">Medium Risk</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {result.clauses.filter(c => c.riskLevel === 'low').length}
            </div>
            <div className="text-sm text-green-600">Low Risk</div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Disclaimer:</strong> This report is for educational purposes only and does not constitute legal advice. 
            Please consult with a qualified attorney for legal decisions and before taking any action based on this analysis.
          </p>
        </div>
      </div>
    </div>
  )
}
