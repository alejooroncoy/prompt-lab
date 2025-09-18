# Prompt Lab - Chatbot Laboratory

Un mini-laboratorio de prompts para experimentar con múltiples LLM providers y analizar respuestas automáticamente.

## 🏗️ Arquitectura

- **Backend**: Python + FastAPI + Clean Architecture (Hexagonal/DDD)
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS v4
- **LLM Providers**: Google Gemini (principal) + Groq (fallback)
- **Base de Datos**: SQLite + Redis (cache)
- **Analytics**: TextBlob + métricas custom

## 🚀 Funcionalidades

- ✅ Chat interface con selector de LLM provider
- ✅ Análisis automático (sentiment, response time, token usage)
- ✅ Historial persistente de conversaciones
- ✅ Dashboard con métricas en tiempo real
- ✅ Export de conversaciones
- ✅ Templates de prompts predefinidos

## 📁 Estructura del Proyecto

```
project-codelab/
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── core/           # Domain Layer (entities, use cases, ports)
│   │   ├── adapters/       # Infrastructure Layer (repositories, external services)
│   │   └── config/         # Configuration
│   ├── tests/              # Test Strategy
│   └── requirements.txt
├── frontend/               # Next.js Frontend
│   ├── src/
│   │   ├── components/     # Atomic Design System
│   │   ├── hooks/          # Custom React Hooks
│   │   ├── services/       # API Layer
│   │   ├── store/          # State Management
│   │   └── types/          # TypeScript Definitions
│   └── package.json
└── docker-compose.yml      # Development Environment
```

## 🛠️ Desarrollo

### Backend (Python)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🐳 Docker

```bash
docker-compose up --build
```

## 📊 Analytics

El sistema analiza automáticamente:
- **Sentiment**: Positivo/Neutro/Negativo (TextBlob)
- **Response Time**: Tiempo de respuesta en ms
- **Token Usage**: Tokens consumidos por provider
- **Quality Metrics**: Longitud, coherencia, etc.

## 🔧 Configuración

1. Copia `.env.example` a `.env`
2. Configura las API keys de los LLM providers
3. Ajusta la configuración de Redis y SQLite
4. Ejecuta las migraciones de base de datos

## 🎯 Demo

El proyecto está preparado para demo en vivo con:
- UI profesional y responsiva
- Error handling robusto
- Analytics en tiempo real
- Fallback automático entre providers
