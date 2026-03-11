# AItelier

An interactive AI-powered platform for collaborative decision-making and research inquiry sessions. AItelier combines Claude AI agents with a modern web interface to facilitate structured conversations, canvas-based ideation, and guided decision-making workflows.

## Features

- **Interactive Sessions**: Create and manage conversation sessions with AI agents
- **Canvas Interface**: Visual workspace for collaborative ideation and brainstorming
- **AI Agents**: Multiple specialized agents including:
  - Decision Challenger: Questions and challenges assumptions
  - Oversight Advisor: Provides oversight and guidance
  - Report Generator: Synthesizes findings and generates reports
  - Reactive Agent: Responds to user queries
  - Intake Agent: Initial information gathering
- **Structured Workflows**: Guided surveys and blueprints for different types of inquiries
- **Event Tracking**: Capture and track interactions during sessions
- **Database Persistence**: Store sessions, events, and user data using SQLModel

## Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) 0.115.0
- **Database ORM**: [SQLModel](https://sqlmodel.tiangolo.com/) 0.0.21
- **AI Integration**: [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) (Claude API)
- **Server**: [Uvicorn](https://www.uvicorn.org/) 0.30.6
- **Environment**: Python with python-dotenv

### Frontend
- **HTML5** with vanilla JavaScript
- **CSS3** with custom styling
- **Config-driven**: Uses `config.js` for API endpoints and settings

### Deployment
- **Frontend**: [Netlify](https://www.netlify.com/)
- **Backend**: [Render](https://render.com/)

## Project Structure

```
.
├── backend/                      # FastAPI application
│   ├── agents/                  # AI agent implementations
│   │   ├── intake.py           # Initial intake agent
│   │   ├── reactive.py         # Reactive response agent
│   │   ├── report_generator.py # Report synthesis
│   │   ├── rq3_decision_challenger.py
│   │   └── rq3_oversight_advisor.py
│   ├── routers/                 # API endpoint routers
│   │   ├── sessions.py         # Session management
│   │   ├── events.py           # Event tracking
│   │   ├── canvas.py           # Canvas interactions
│   │   ├── guidance.py         # Guidance endpoints
│   │   ├── blueprint.py        # Blueprint workflows
│   │   └── survey.py           # Survey endpoints
│   ├── main.py                 # FastAPI app initialization
│   ├── database.py             # Database setup
│   ├── models.py               # SQLModel data models
│   ├── requirements.txt        # Python dependencies
│   └── test_e2e.py             # End-to-end tests
├── frontend/                    # Web interface
│   ├── index.html              # Main session page
│   ├── canvas.html             # Canvas workspace
│   ├── blueprint.html          # Blueprint interface
│   ├── survey.html             # Survey interface
│   ├── config.js               # Configuration
│   └── style.css               # Styling
├── netlify.toml                # Netlify configuration
└── render.yaml                 # Render deployment config
```

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js (for frontend development)
- Anthropic API key

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/cyanghec/aitelier.git
   cd aitelier
   ```

2. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create a .env file in the backend directory
   echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
   ```

4. **Run the development server**
   ```bash
   python -m uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Configure the API endpoint** in `frontend/config.js`
   ```javascript
   // Update the API_URL to point to your backend
   const API_URL = 'http://localhost:8000';
   ```

2. **Start a local server** (using Python)
   ```bash
   cd frontend
   python -m http.server 8080
   ```
   Or use any HTTP server of your choice (Node.js http-server, VS Code Live Server, etc.)

3. **Access the application**
   Open `http://localhost:8080` in your browser

## API Endpoints

### Sessions
- `GET /sessions` - List all sessions
- `POST /sessions` - Create a new session
- `GET /sessions/{id}` - Get session details
- `PUT /sessions/{id}` - Update a session

### Events
- `POST /events` - Record an event
- `GET /sessions/{session_id}/events` - Get session events

### Canvas
- `POST /canvas` - Create canvas content
- `GET /canvas/{id}` - Retrieve canvas

### Guidance
- `POST /guidance` - Request guidance from AI agents

### Blueprint
- `GET /blueprints` - List available blueprints
- `POST /blueprints/{id}/start` - Start a blueprint workflow

### Survey
- `GET /surveys` - List surveys
- `POST /surveys/{id}/submit` - Submit survey responses

### Health
- `GET /health` - API health check

For complete API documentation, run the backend and visit `/docs` (Swagger UI).

## Development

### Running Tests
```bash
cd backend
python -m pytest test_e2e.py
```

### Database
The application uses SQLModel with a SQLite database (by default, see `database.py` for configuration).

### Adding New Agents
1. Create a new agent file in `backend/agents/`
2. Implement the agent logic using the Anthropic SDK
3. Import and use the agent in the appropriate router

### Adding New Routes
1. Create a new router file in `backend/routers/`
2. Define FastAPI routes and handlers
3. Include the router in `backend/main.py`

## Configuration

Key configuration files:
- **Backend**: `backend/main.py` - CORS settings, router registration
- **Frontend**: `frontend/config.js` - API URLs and client settings
- **Deployment**: `netlify.toml`, `render.yaml` - Platform-specific configs

## Environment Variables

Required environment variables (in `backend/.env`):
- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude access

## Deployment

### Frontend (Netlify)
The frontend is automatically deployed to Netlify when you push to the main branch.

### Backend (Render)
The backend is configured for deployment on Render. Update `render.yaml` with your service details.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Contact

For questions or issues, please contact [Add contact information].
