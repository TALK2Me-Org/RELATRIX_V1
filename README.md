# RELATRIX - Relationship Intelligence Platform

RELATRIX is an AI-powered relationship counseling platform that uses specialized agents to help couples communicate better, resolve conflicts, and strengthen their relationships.

## Features

- **7 Specialized AI Agents** for different relationship scenarios
- **Intelligent Agent Switching** based on conversation context
- **Memory-Optimized Conversations** using Mem0 + Redis
- **Real-time Chat Interface** with WebSocket support
- **Admin Dashboard** for monitoring and management
- **Cost Tracking** and usage analytics
- **Supabase Authentication** for secure user management

## Architecture

### Core Components

1. **MCP Server** - Model Context Protocol server managing agent interactions
2. **Specialized Agents** - 7 AI agents for different relationship scenarios
3. **Memory Manager** - Intelligent context preservation using Mem0 + Redis
4. **FastAPI Backend** - RESTful API with WebSocket support
5. **React Frontend** - Modern chat interface with admin panel

### Specialized Agents

1. **Misunderstanding Protector** - Analyzes and prevents communication issues
2. **Emotional Vomit Dumper** - Safe space for emotional release
3. **Conflict Solver** - Mediates and resolves relationship conflicts
4. **Solution Finder** - Creates actionable plans for relationship improvement
5. **Communication Simulator** - Practice conversations in safe environment
6. **Relationship Upgrader** - Gamified relationship enhancement
7. **Breakthrough Manager** - Crisis support and recovery planning

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Redis
- PostgreSQL
- Railway account (for deployment)

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd RELATRIX_V1
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

5. Start services with Docker:
```bash
docker-compose up -d
```

6. Run the backend:
```bash
cd backend
uvicorn app.main:app --reload
```

7. Run the frontend:
```bash
cd frontend
npm start
```

### External Services Setup

You'll need to set up these external services:

1. **OpenAI API** - For AI agent capabilities
2. **Mem0** - For intelligent memory management
3. **Supabase** - For authentication and user management
4. **Railway** - For deployment and hosting

See the deployment documentation for detailed setup instructions.

## API Endpoints

### Chat API
- `POST /chat/send` - Send message to AI agent
- `GET /chat/history` - Get conversation history
- `WebSocket /chat/ws` - Real-time chat connection

### Admin API
- `GET /admin/users` - User management
- `GET /admin/analytics` - Usage analytics
- `GET /admin/settings` - System configuration

## Deployment

This application is designed to be deployed on Railway. See `docs/deployment-railway.md` for detailed deployment instructions.

## Cost Optimization

- **Memory Management** - Intelligent context compression
- **Agent Switching** - Efficient context preservation
- **Redis Caching** - Reduced API calls
- **Usage Tracking** - Real-time cost monitoring

## Security

- **Supabase Authentication** - Secure user management
- **JWT Tokens** - API security
- **Admin Role Protection** - Secure admin access
- **Environment Variables** - Secure configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary and confidential.

## Support

For support and questions, please contact the development team.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI       │    │   MCP Server    │
│   - Chat UI      │◄──►│   - REST API    │◄──►│   - 7 Agents    │
│   - Admin Panel  │    │   - WebSocket   │    │   - Memory Mgr  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │                        ▼                        ▼
        │              ┌─────────────────┐    ┌─────────────────┐
        │              │   Supabase      │    │   Mem0 + Redis  │
        │              │   - Auth        │    │   - Memory      │
        │              │   - User Data   │    │   - Context     │
        │              └─────────────────┘    └─────────────────┘
        │
        ▼
┌─────────────────┐
│   Railway       │
│   - Deployment  │
│   - PostgreSQL  │
│   - Redis       │
└─────────────────┘
```