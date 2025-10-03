# WebIntel Analytics - Angular Frontend

This is the Angular frontend for the WebIntel Analytics application, providing a modern web interface for comprehensive content analysis and strategic question generation.

## Features

- 🌐 Modern Angular 17+ application with standalone components
- 🎨 Dark/Light theme toggle with system preference detection
- 📱 Responsive design that works on desktop and mobile
- ⚡ Real-time job status monitoring and progress tracking
- 📥 File download functionality for analysis results
- 🔧 Advanced configuration options with collapsible sections
- 🎯 Material Design components for consistent UI/UX

## Prerequisites

- Node.js 18+ and npm
- Angular CLI (`npm install -g @angular/cli`)

## Installation

1. Navigate to the angular-frontend directory:
```bash
cd angular-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Install Angular CLI globally (if not already installed):
```bash
npm install -g @angular/cli
```

## Development

Start the development server:
```bash
npm start
# or
ng serve
```

The application will be available at `http://localhost:4200`

## Build

Build the project for production:
```bash
npm run build
# or
ng build --configuration production
```

The build artifacts will be stored in the `dist/` directory.

## Configuration

The frontend is configured to connect to the Node.js backend at `http://localhost:3000`. If you need to change this, update the `baseUrl` in `src/app/services/api.service.ts`.

## Project Structure

```
src/
├── app/
│   ├── models/           # TypeScript interfaces and models
│   ├── services/         # Angular services for API and theme
│   ├── app.component.*   # Main application component
│   └── ...
├── assets/              # Static assets
├── styles.scss          # Global styles and theme variables
└── index.html          # Main HTML file
```

## Features Implemented

### Core Functionality
- ✅ Website URL input with validation
- ✅ Question types configuration
- ✅ Output format selection (Excel)
- ✅ Analysis options (Analysis Questions, Critical Thinking)
- ✅ Advanced scraping options (scroll pages, crawling, depth control)
- ✅ Retrieval & validation settings
- ✅ Test case generation configuration
- ✅ Real-time job monitoring
- ✅ File download functionality

### UI/UX Features
- ✅ Dark/Light theme toggle
- ✅ Responsive design
- ✅ Progress indicators
- ✅ Status notifications
- ✅ Error handling
- ✅ Form validation
- ✅ Collapsible advanced options

## Theme System

The application supports both light and dark themes:
- Automatic system preference detection
- Manual toggle in the top-right corner
- Persistent theme selection (saved to localStorage)
- Smooth transitions between themes

## API Integration

The frontend communicates with the Node.js backend which proxies requests to the Python FastAPI backend:

```
Angular Frontend (4200) → Node.js Backend (3000) → Python FastAPI (8000)
```

This architecture provides:
- Better CORS handling
- Request/response logging
- Error handling and transformation
- Future extensibility for additional features

## Troubleshooting

### Backend Connection Issues
If you see "Backend server is not running" error:
1. Ensure the Node.js backend is running on port 3000
2. Ensure the Python backend is running on port 8000
3. Check that CORS is properly configured

### Build Issues
If you encounter build errors:
1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Clear Angular cache: `ng cache clean`
3. Update Angular CLI: `npm update -g @angular/cli`

## Contributing

1. Follow Angular style guide
2. Use TypeScript strict mode
3. Implement proper error handling
4. Add appropriate type definitions
5. Test on both light and dark themes
6. Ensure responsive design works on mobile devices
