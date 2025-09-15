export interface ClauseAnalysis {
  id: string
  type: string
  originalText: string
  plainLanguage: string
  riskLevel: 'high' | 'medium' | 'low'
  riskReason: string
  recommendations: string[]
  citations?: string[]
}

export interface DocumentAnalysisResult {
  documentId: string
  fileName: string
  documentType: string
  overallRisk: 'high' | 'medium' | 'low'
  clauses: ClauseAnalysis[]
  keyFindings: string[]
  summary: string
  processedAt: string
}

export interface QAResponse {
  question: string
  answer: string
  confidence: number
  sources: string[]
}

export interface UploadResponse {
  success: boolean
  documentId: string
  message: string
}
