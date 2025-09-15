# Nayaya.ai Frontend

This is the frontend application for Nayaya.ai, built with Next.js 13+ and Tailwind CSS.

## 🚀 Getting Started

### Prerequisites

- Node.js 18 or later
- npm or yarn

### Environment Setup

1. **Copy environment file:**
   ```bash
   cp .env.example .env.local
   ```

2. **Update environment variables:**
   ```bash
   # For local development
   NEXT_PUBLIC_API_URL=http://localhost:8000
   
   # For production (update with your Cloud Run backend URL)
   NEXT_PUBLIC_API_URL=https://your-backend-url.run.app
   ```

### Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Building for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js 13+ App Router
│   ├── components/         # React components
│   │   ├── DocumentUpload.tsx
│   │   ├── DocumentAnalysis.tsx
│   │   ├── ClauseCard.tsx
│   │   ├── QASection.tsx
│   │   └── ExportReport.tsx
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   └── types.ts            # TypeScript types
├── public/                 # Static assets
├── .env.example            # Environment template
├── .env.local.example      # Local dev template
├── next.config.js          # Next.js configuration
├── tailwind.config.js      # Tailwind CSS config
├── package.json            # Dependencies
└── Dockerfile              # Container configuration
```

## 🎨 UI Components

### DocumentUpload
- Drag & drop file upload
- File validation (PDF, DOC, DOCX)
- Upload progress tracking
- Error handling

### DocumentAnalysis
- Tabbed interface (Overview, Clauses, Q&A, Export)
- Risk assessment visualization
- Clause-by-clause breakdown
- Interactive Q&A system

### ClauseCard
- Color-coded risk levels
- Expandable clause details
- Plain language explanations
- Recommendations display

### QASection
- Real-time question answering
- Suggested questions
- Confidence scores
- Source citations

### ExportReport
- PDF generation
- Report preview
- Download functionality
- Print support

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NODE_ENV` | Environment mode | `development` |
| `NEXT_PUBLIC_APP_NAME` | Application name | `Nayaya.ai` |
| `NEXT_PUBLIC_MAX_FILE_SIZE_MB` | Max upload size | `10` |

### Next.js Configuration

The `next.config.js` includes:
- Standalone output for Docker
- Security headers
- Image optimization
- Webpack customizations for PDF handling

## 🎨 Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Responsive Design**: Mobile-first approach
- **Color Scheme**: 
  - Primary: Blue (`#3b82f6`)
  - Success: Green (`#10b981`)
  - Warning: Yellow (`#f59e0b`)
  - Danger: Red (`#ef4444`)

### Risk Level Colors

```css
.risk-high { @apply bg-red-100 border-red-300 text-red-800; }
.risk-medium { @apply bg-yellow-100 border-yellow-300 text-yellow-800; }
.risk-low { @apply bg-green-100 border-green-300 text-green-800; }
```

## 📱 Features

### Document Processing Flow
1. **Upload**: Drag & drop or click to upload
2. **Processing**: Real-time progress with status updates
3. **Analysis**: Display results with risk assessment
4. **Interaction**: Q&A and detailed clause exploration
5. **Export**: Generate and download PDF reports

### Responsive Design
- Mobile-optimized interface
- Touch-friendly interactions
- Adaptive layouts for all screen sizes

### Accessibility
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- High contrast support

## 🚀 Deployment

### Docker Deployment

```bash
# Build Docker image
docker build -t nayaya-frontend .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=https://your-backend.run.app nayaya-frontend
```

### Google Cloud Run

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/nayaya-frontend
gcloud run deploy nayaya-frontend --image gcr.io/PROJECT_ID/nayaya-frontend --platform managed
```

## 🧪 Testing

### Running Tests

```bash
# Run unit tests
npm test

# Run tests in watch mode
npm test -- --watch

# Generate coverage report
npm test -- --coverage
```

### Test Structure

```
__tests__/
├── components/
│   ├── DocumentUpload.test.tsx
│   ├── ClauseCard.test.tsx
│   └── QASection.test.tsx
├── pages/
│   └── index.test.tsx
└── utils/
    └── api.test.ts
```

## 🔍 Debugging

### Development Tools

1. **React DevTools**: Browser extension for React debugging
2. **Next.js Debug**: Built-in debugging with `DEBUG=*`
3. **Console Logs**: Detailed logging in development mode

### Common Issues

1. **API Connection**: Check `NEXT_PUBLIC_API_URL` in `.env.local`
2. **Build Errors**: Verify all dependencies are installed
3. **Styling Issues**: Check Tailwind CSS configuration

## 📚 Dependencies

### Core Dependencies
- `next`: React framework
- `react`: UI library
- `tailwindcss`: CSS framework
- `axios`: HTTP client
- `react-dropzone`: File upload
- `jspdf`: PDF generation

### Development Dependencies
- `typescript`: Type checking
- `eslint`: Code linting
- `@types/*`: TypeScript definitions

## 🤝 Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Write tests for new components
4. Update documentation as needed

## 📄 License

MIT License - see the LICENSE file for details.
