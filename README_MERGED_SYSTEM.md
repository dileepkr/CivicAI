# CivicAI Policy Debate System - Merged Backend & Frontend

## Overview

This is a fully integrated policy debate system that combines the powerful backend agentic debate systems with a modern React frontend. The system provides real-time policy analysis, stakeholder debates, and email generation capabilities.

## Architecture

### Backend (FastAPI)
- **Location**: `api/main.py`
- **Port**: 8000
- **Features**:
  - RESTful API endpoints for policies, debates, and sessions
  - WebSocket support for real-time debate streaming
  - Session management with unique debate IDs
  - Integration with all three debate systems (debug, weave, human)

### Frontend (React/TypeScript)
- **Location**: `policy-pulse-debate/`
- **Port**: 5173
- **Features**:
  - Three-panel interface (PolicyList, DebatePanel, EmailGenerator)
  - Real-time WebSocket connections for live debate streaming
  - System selection dropdown (debug, weave, human)
  - Responsive design with Tailwind CSS

### Debate Systems
- **Debug System**: Simple stakeholder simulation with mock debates
- **Weave System**: Advanced AI-powered debate with tracking and analysis
- **Human System**: Interactive debates with human participation

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- UV package manager (auto-installed by script)

### Installation & Running
```bash
# Make the startup script executable
chmod +x start_system.sh

# Start the entire system
./start_system.sh
```

The script will:
1. Install UV if not present
2. Create Python virtual environment
3. Install all Python dependencies
4. Install Node.js dependencies
5. Start both backend and frontend services
6. Open the system in your browser

### Manual Installation
If you prefer to install manually:

```bash
# Backend setup
uv venv
source .venv/bin/activate
uv pip install -e .

# Frontend setup
cd policy-pulse-debate
npm install
cd ..

# Start backend
cd api && python main.py &

# Start frontend
cd policy-pulse-debate && npm run dev
```

## Usage

### 1. Access the System
- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 2. Running a Debate
1. Select a policy from the left panel
2. Choose a debate system from the dropdown
3. Click "Start Debate" to begin
4. Watch the real-time debate in the middle panel
5. Generate emails from the debate results in the right panel

### 3. Available Policies
- `policy_1`: Housing Policy with stakeholder perspectives
- `policy_2`: Environmental Policy with regulatory impacts

## API Endpoints

### REST Endpoints
- `GET /policies` - List all available policies
- `GET /policies/{policy_id}` - Get specific policy details
- `POST /debates/start` - Start a new debate session
- `GET /debates/{session_id}/status` - Get debate status
- `GET /debates/{session_id}/messages` - Get debate messages

### WebSocket Endpoints
- `WS /debates/{session_id}/stream` - Real-time debate streaming

## Project Structure

```
CivicAI/
├── api/
│   ├── main.py                 # FastAPI backend
│   └── requirements.txt        # API dependencies
├── policy-pulse-debate/        # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── PolicyList.tsx
│   │   │   ├── DebatePanel.tsx
│   │   │   └── EmailGenerator.tsx
│   │   └── services/
│   │       └── api.ts          # API client
│   └── package.json
├── src/dynamic_crew/           # Backend debate systems
│   ├── debate/
│   │   ├── base.py
│   │   └── systems/
│   │       ├── debug.py
│   │       ├── weave.py
│   │       └── human.py
│   └── tools/
├── test_data/                  # Policy test data
│   ├── policy_1.json
│   └── policy_2.json
├── pyproject.toml             # Python dependencies
└── start_system.sh            # Startup script
```

## Key Features

### Real-time Debate Streaming
- WebSocket connections provide live updates
- Messages appear instantly in the UI
- Auto-reconnection on connection loss

### Multi-System Support
- Debug: Fast simulation for testing
- Weave: Advanced AI with analysis tracking
- Human: Interactive debates with user input

### Email Generation
- Automatic stakeholder detection from debates
- Professional email templates
- Customizable based on debate outcomes

### Session Management
- Unique session IDs for each debate
- Session state tracking
- Message history preservation

## Development

### Adding New Debate Systems
1. Create new system in `src/dynamic_crew/debate/systems/`
2. Extend `BaseDebateSystem` class
3. Add to system selection in `DebatePanel.tsx`
4. Update API routing in `api/main.py`

### Adding New Policies
1. Add JSON file to `test_data/`
2. Follow existing policy structure
3. System will automatically detect and load

## Troubleshooting

### Common Issues

**Backend not starting**
- Check Python version (3.10+ required)
- Verify all dependencies installed
- Check port 8000 availability

**Frontend not connecting**
- Ensure backend is running first
- Check WebSocket connection in browser dev tools
- Verify API endpoints are accessible

**UV installation issues**
- Manually install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Add to PATH: `export PATH="$HOME/.cargo/bin:$PATH"`

**Dependencies conflicts**
- Clear virtual environment: `rm -rf .venv`
- Reinstall: `uv venv && uv pip install -e .`

### Performance Tips
- Use UV for 10-20x faster package installation
- Enable debug mode for faster development iteration
- Use WebSocket for real-time updates instead of polling

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the full system
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review API documentation at http://localhost:8000/docs
- Check browser console for frontend errors
- Verify backend logs for API issues 