# FinScope AI Frontend - Phase 9

React frontend application for FinScope AI with three-panel layout, real-time WebSocket updates, and full backend integration.

## Features

- ✅ Three-panel layout (History | Main | Activity/Sources)
- ✅ Chat interface for query input
- ✅ Plan selection UI with clarification questions
- ✅ Real-time progress bar with WebSocket
- ✅ Activity feed with live updates (URLs, tools, progress)
- ✅ Sources panel with citations (15+ sources)
- ✅ Report viewer with markdown rendering
- ✅ History persistence across sessions
- ✅ Responsive design for mobile devices
- ✅ WebSocket auto-reconnection

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env` file in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173` (or the port Vite assigns).

### 4. Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Usage

### Test Flow

1. **Enter Query**: Type "Analyze TCS vs Infosys cloud services" in the query input
2. **Auto-Classification**: Query is automatically classified (IT sector)
3. **Plan Generation**: Deep plan with clarification questions is displayed
4. **Select Questions**: Choose 2-3 clarification questions
5. **Start Research**: Click "Start Deep Research"
6. **Real-Time Updates**: 
   - Progress bar shows research steps
   - Activity panel shows URLs being accessed
   - Tool execution updates appear
7. **Report Display**: Report appears on completion
8. **Sources**: Sources panel shows all citations with URLs

## Project Structure

```
src/
├── components/
│   ├── Layout/          # Three-panel layout
│   ├── Chat/            # Query input, plan selection, progress, report
│   ├── Activity/        # Real-time activity feed
│   └── Sources/         # Citations and sources
├── hooks/
│   ├── useResearch.ts   # Main research workflow hook
│   └── useLocalStorage.ts # Local storage persistence
├── services/
│   ├── api.ts           # REST API client
│   └── websocket.ts     # WebSocket client
├── types/               # TypeScript type definitions
└── App.tsx              # Main app component
```

## API Integration

### REST Endpoints
- `POST /api/classify` - Query classification
- `POST /api/plan` - Generate research plan
- `POST /api/research/start` - Start research (fallback)
- `GET /api/report/{id}` - Get report
- `GET /api/report` - List all reports
- `POST /api/report/export` - Export report

### WebSocket
- `ws://localhost:8000/api/research/stream` - Real-time updates

## Requirements

- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000`

## Troubleshooting

### WebSocket Connection Issues
- Ensure backend is running
- Check CORS settings in backend
- Verify WebSocket URL in `.env`

### API Errors
- Check backend is accessible
- Verify API URL in `.env`
- Check browser console for errors

### Build Issues
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf .vite`
