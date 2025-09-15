'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { CloudArrowUpIcon, DocumentTextIcon } from '@heroicons/react/24/outline'
import { DocumentAnalysisResult } from '../types'
import axios from 'axios'

interface DocumentUploadProps {
  onAnalysisStart: () => void
  onAnalysisComplete: (result: DocumentAnalysisResult) => void
  isAnalyzing: boolean
}

export default function DocumentUpload({ 
  onAnalysisStart, 
  onAnalysisComplete, 
  isAnalyzing 
}: DocumentUploadProps) {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    onAnalysisStart()
    
    try {
      const formData = new FormData()
      formData.append('document', file)

      // Step 1: Upload document
      setCurrentStep('Uploading document...')
      setUploadProgress(20)

      const uploadResponse = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      )

      const { documentId } = uploadResponse.data

      // Step 2: OCR Processing
      setCurrentStep('Extracting text with Document AI...')
      setUploadProgress(40)

      await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/process-ocr`, {
        documentId
      })

      // Step 3: Clause Classification
      setCurrentStep('Classifying clauses with Vertex AI...')
      setUploadProgress(60)

      await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/classify-clauses`, {
        documentId
      })

      // Step 4: Risk Analysis & Generation
      setCurrentStep('Generating plain language explanations...')
      setUploadProgress(80)

      const analysisResponse = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/analyze`, {
        documentId
      })

      setCurrentStep('Complete!')
      setUploadProgress(100)

      // Mock response for development
      const mockResult: DocumentAnalysisResult = {
        documentId,
        fileName: file.name,
        documentType: 'Rental Agreement',
        overallRisk: 'medium',
        summary: 'This rental agreement contains standard terms with some areas requiring attention, particularly around security deposits and early termination fees.',
        keyFindings: [
          'Security deposit is non-refundable under certain conditions',
          'Early termination fee equals 2 months rent',
          'Landlord can increase rent with 30 days notice'
        ],
        clauses: [
          {
            id: '1',
            type: 'Security Deposit',
            originalText: 'Tenant shall pay a security deposit equal to two (2) months rent, which shall be forfeited in the event of breach of any term herein.',
            plainLanguage: 'You need to pay 2 months rent upfront as a security deposit. If you break any rule in this contract, you lose this money completely.',
            riskLevel: 'high',
            riskReason: 'Complete forfeiture of security deposit for any breach is excessive and may not be legally enforceable',
            recommendations: [
              'Negotiate for partial forfeiture based on actual damages',
              'Request itemized list of potential deductions',
              'Check local tenant protection laws'
            ],
            citations: ['State Tenant Rights Act Section 12.3']
          },
          {
            id: '2',
            type: 'Rent Increase',
            originalText: 'Landlord reserves the right to increase rent upon thirty (30) days written notice to Tenant.',
            plainLanguage: 'Your landlord can raise your rent anytime with just 30 days notice.',
            riskLevel: 'medium',
            riskReason: 'No limit on rent increase amount could lead to significant financial burden',
            recommendations: [
              'Negotiate a cap on annual rent increases',
              'Request longer notice period (60-90 days)',
              'Consider fixed-term lease to prevent increases'
            ]
          }
        ],
        processedAt: new Date().toISOString()
      }

      setTimeout(() => {
        onAnalysisComplete(mockResult)
      }, 1000)

    } catch (error) {
      console.error('Analysis failed:', error)
      setCurrentStep('Analysis failed. Please try again.')
      setTimeout(() => {
        setCurrentStep('')
        setUploadProgress(0)
      }, 3000)
    }
  }, [onAnalysisStart, onAnalysisComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1,
    disabled: isAnalyzing
  })

  if (isAnalyzing) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-6"></div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Analyzing Your Document
            </h3>
            <p className="text-gray-600 mb-6">{currentStep}</p>
            
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div 
                className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            
            <div className="text-sm text-gray-500">
              This may take 30-60 seconds as we process your document with Google Cloud AI
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${isDragActive 
            ? 'border-primary-400 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
        `}
      >
        <input {...getInputProps()} />
        
        <CloudArrowUpIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Upload Legal Document
        </h3>
        
        <p className="text-gray-600 mb-4">
          {isDragActive 
            ? 'Drop your document here...' 
            : 'Drag and drop your document, or click to browse'
          }
        </p>
        
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
          <DocumentTextIcon className="h-5 w-5" />
          <span>Supports PDF, DOC, DOCX up to 10MB</span>
        </div>
      </div>

      <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Important Disclaimer
            </h3>
            <p className="mt-1 text-sm text-yellow-700">
              Nayaya.ai is an educational tool that simplifies legal text. It does not provide legal advice. 
              Please consult a qualified lawyer for decisions with legal consequences.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
