# Energy Conservation API

A comprehensive REST API for energy conservation applications with AI-powered recommendations using OpenAI integration and MongoDB database.

## Features

- **Energy Data Management**: Track energy consumption and production data from various devices
- **Device Management**: Monitor and manage energy-consuming devices (HVAC, lighting, appliances, etc.)
- **User Management**: Handle user accounts with energy goals and preferences
- **AI-Powered Recommendations**: Get personalized energy conservation recommendations using OpenAI
- **Energy Analytics**: Analyze energy patterns and compare usage across time periods
- **Real-time Statistics**: Get comprehensive energy statistics and daily breakdowns

## Tech Stack

- **FastAPI**: Modern Python web framework
- **MongoDB**: NoSQL database with Motor for async operations
- **OpenAI API**: AI-powered energy recommendations
- **Pydantic**: Data validation and serialization
- **Motor**: Async MongoDB driver

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB 4.4+
- OpenAI API key (optional but recommended for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd energy-conservation-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up MongoDB**
   ```bash
   # Install MongoDB (Ubuntu/Debian)
   sudo apt-get install mongodb
   
   # Or use Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   
   # Update MONGODB_URL in .env file
   MONGODB_URL=mongodb://localhost:27017/energy_conservation_db
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Configuration

Edit the `.env` file with your settings:

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017/energy_conservation_db
DATABASE_NAME=energy_conservation_db

# OpenAI (for AI features)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Security
SECRET_KEY=your-secret-key-here

# Application
DEBUG=False
ENVIRONMENT=production
```

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## API Endpoints

### Core Energy Management

#### Users
- `POST /api/v1/energy/users/` - Create user
- `GET /api/v1/energy/users/` - List users
- `GET /api/v1/energy/users/{user_id}` - Get user with devices
- `PUT /api/v1/energy/users/{user_id}` - Update user
- `DELETE /api/v1/energy/users/{user_id}` - Delete user

#### Devices
- `POST /api/v1/energy/users/{user_id}/devices/` - Add device
- `GET /api/v1/energy/users/{user_id}/devices/` - List user devices
- `GET /api/v1/energy/devices/{device_id}` - Get device with energy data
- `PUT /api/v1/energy/devices/{device_id}` - Update device
- `DELETE /api/v1/energy/devices/{device_id}` - Delete device

#### Energy Data
- `POST /api/v1/energy/devices/{device_id}/energy-data/` - Record energy data
- `GET /api/v1/energy/devices/{device_id}/energy-data/` - Get device energy data
- `GET /api/v1/energy/users/{user_id}/energy-data/` - Get user energy data

#### Statistics
- `GET /api/v1/energy/users/{user_id}/energy-stats/` - Get energy statistics
- `GET /api/v1/energy/users/{user_id}/daily-stats/` - Get daily statistics

### AI-Powered Features

#### Recommendations
- `POST /api/v1/ai/users/{user_id}/recommendations` - Get AI recommendations
- `POST /api/v1/ai/users/{user_id}/energy-analysis` - Analyze energy patterns
- `POST /api/v1/ai/devices/{device_id}/optimization-tips` - Get device optimization tips
- `POST /api/v1/ai/users/{user_id}/compare-usage` - Compare usage periods
- `GET /api/v1/ai/users/{user_id}/efficiency-report` - Get comprehensive efficiency report

#### AI Service
- `GET /api/v1/ai/ai-status` - Check AI service status

## Data Models

### User
- Personal information and energy preferences
- Energy goals and preferred settings
- Associated devices and energy data

### Device
- Device type (HVAC, lighting, appliances, etc.)
- Location and specifications
- Smart device capabilities

### Energy Data
- Real-time consumption and production data
- Power measurements and environmental data
- Cost tracking and timestamps

## AI Features

The API integrates with OpenAI to provide:

1. **Personalized Recommendations**: Analyze user behavior and suggest energy-saving actions
2. **Pattern Analysis**: Identify trends and anomalies in energy usage
3. **Device Optimization**: Provide device-specific efficiency tips
4. **Usage Comparisons**: Compare energy usage across different time periods
5. **Efficiency Reports**: Comprehensive analysis with actionable insights

## Development

### Project Structure
```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── database.py          # MongoDB setup and connection
├── models/              # Pydantic models for MongoDB
│   ├── users.py
│   ├── devices.py
│   └── energy_data.py
├── schemas/             # Pydantic schemas
│   └── energy.py
├── routers/             # API route handlers
│   ├── energy.py
│   └── ai_recommendations.py
└── services/            # Business logic
    └── openai_service.py
```

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Docker (Coming Soon)
```bash
docker build -t energy-conservation-api .
docker run -p 8000:8000 energy-conservation-api
```

### Production Considerations

1. **Database**: Use a managed MongoDB service (MongoDB Atlas, AWS DocumentDB, etc.)
2. **Environment Variables**: Secure API keys and database credentials
3. **Monitoring**: Add logging and health checks
4. **Security**: Implement authentication and rate limiting
5. **Scaling**: Consider horizontal scaling for high traffic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.