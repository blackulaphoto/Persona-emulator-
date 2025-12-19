# Persona Evolution Simulator

> Explore how life experiences and therapeutic interventions shape personality over time using AI-powered psychological analysis.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Tests](https://img.shields.io/badge/tests-41%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

The Persona Evolution Simulator is a research and educational tool that models psychological development through life experiences and therapeutic interventions. Built with evidence-based psychology and powered by GPT-4, it demonstrates realistic personality evolution, trauma impacts, and therapy outcomes.

### Key Features

- **🧠 AI-Powered Analysis**: GPT-4 analyzes experiences using developmental psychology and trauma research
- **📊 Big Five Personality Tracking**: Watch how openness, conscientiousness, extraversion, agreeableness, and neuroticism evolve
- **🏥 Realistic Therapy Modeling**: 8 evidence-based therapeutic modalities with research-backed efficacy rates
- **📈 Timeline Visualization**: Complete chronological view of psychological evolution
- **🔬 Scientifically Grounded**: Based on developmental stages, attachment theory, and therapeutic research

## Quick Start

### Prerequisites

- Python 3.11.8
- Node.js 18+
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/persona-evolution-simulator.git
cd persona-evolution-simulator

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Frontend setup
cd ../frontend
npm install
```

### Running Locally

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## How It Works

### 1. Create a Persona

Define a baseline:
- Name, age, gender
- Background story
- Initial personality traits (optional)

### 2. Add Life Experiences

Describe events:
- "Parents divorced when I was 10"
- "Started college at 18, struggled with social anxiety"
- "Experienced car accident at 25"

AI analyzes each experience for:
- Psychological impact (Big Five trait changes)
- Symptom development (anxiety, depression, etc.)
- Long-term patterns (trust issues, fear responses)
- Recommended therapies

### 3. Apply Therapeutic Interventions

Choose from 8 evidence-based therapies:
- **CBT**: Cognitive Behavioral Therapy
- **ACT**: Acceptance & Commitment Therapy
- **EMDR**: Eye Movement Desensitization
- **IFS**: Internal Family Systems
- **DBT**: Dialectical Behavior Therapy
- **Psychodynamic**: Psychodynamic Therapy
- **Somatic Experiencing**: Body-focused trauma therapy
- **ERP**: Exposure & Response Prevention

Each therapy has:
- Specific efficacy rates for different symptoms
- Realistic symptom reduction (partial, not complete)
- Limitations (e.g., CBT addresses symptoms but not root trauma)

### 4. Watch Evolution

View complete timeline:
- Chronological life events
- Personality changes over time
- Symptom severity progression
- Therapy effectiveness

## Example Use Cases

### 1. Therapy Education

Students can:
- Explore how different therapies work
- Understand therapy limitations
- See why matched therapy matters
- Learn about trauma-informed care

### 2. Research Simulation

Researchers can:
- Model intervention outcomes
- Test therapeutic hypotheses
- Analyze developmental impacts
- Compare treatment approaches

### 3. Case Study Development

Clinicians can:
- Create teaching examples
- Demonstrate treatment planning
- Show realistic recovery arcs
- Illustrate complex trauma

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Frontend                          │
│  Next.js 14 + React + TypeScript + Tailwind         │
│  Beautiful UI with earth-tone aesthetic             │
└─────────────────┬────────────────────────────────────┘
                  │ REST API
┌─────────────────▼────────────────────────────────────┐
│                    Backend                           │
│  FastAPI + SQLAlchemy + OpenAI GPT-4                │
│  Psychology engines + Therapy database               │
└─────────────────┬────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────┐
│                  Database                            │
│  SQLite (dev) / PostgreSQL (prod)                   │
│  Personas, Experiences, Interventions, Snapshots    │
└──────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11.8)
- **Database**: SQLAlchemy ORM + SQLite/PostgreSQL
- **AI**: OpenAI GPT-4o
- **Testing**: Pytest (41/41 tests passing)

### Frontend
- **Framework**: Next.js 14 (React 18, TypeScript)
- **Styling**: Tailwind CSS with custom design system
- **Animation**: Framer Motion + CSS animations
- **Icons**: Lucide React

## Project Structure

```
persona-evolution-simulator/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # REST API endpoints
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # AI analysis engines
│   │   └── core/              # Config, database
│   ├── tests/                 # 41 comprehensive tests
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx          # Landing page
│   │   ├── create/           # Persona creation
│   │   └── persona/[id]/     # Timeline view
│   ├── lib/
│   │   └── api.ts            # API client
│   └── package.json
└── DEPLOYMENT.md             # Deployment guide
```

## API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Key Endpoints

```
POST   /api/v1/personas                     Create persona
GET    /api/v1/personas                     List personas
GET    /api/v1/personas/{id}                Get persona
POST   /api/v1/personas/{id}/experiences    Add experience
POST   /api/v1/personas/{id}/interventions  Add intervention
GET    /api/v1/personas/{id}/timeline       Get timeline
```

## Testing

### Backend Tests

```bash
cd backend
PYTHONPATH=. pytest tests/ -v

# Output:
# 41 passed in 8.03s
# - 11 persona tests
# - 9 experience tests
# - 10 intervention tests
# - 11 timeline tests
```

### Frontend (Manual)

The frontend is designed for real-world usage and is tested through:
- User acceptance testing
- Cross-browser compatibility
- Mobile responsiveness
- Accessibility audit

## Scientific Accuracy

### Evidence-Based Foundations

1. **Developmental Psychology**
   - Age-based trauma impact multipliers
   - Critical periods for attachment formation
   - Neuroplasticity considerations

2. **Trauma Research**
   - ACE (Adverse Childhood Experiences) framework
   - Developmental trauma disorder criteria
   - Attachment theory (Bowlby, Ainsworth)

3. **Therapeutic Efficacy**
   - Research-backed success rates
   - Specific symptom targeting
   - Realistic partial relief modeling

### What This Is NOT

- ❌ A substitute for real therapy
- ❌ A diagnostic tool
- ❌ Medical advice
- ❌ A predictive model for real people

### What This IS

- ✅ An educational simulation
- ✅ A research tool
- ✅ A demonstration of psychological principles
- ✅ A learning platform

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.

**Quick Deploy Options:**
- Railway (recommended): `railway up`
- Vercel + Railway: Frontend on Vercel, backend on Railway
- Docker: `docker-compose up`

**Estimated Costs:**
- Hobby: ~$15-30/month
- Production: ~$160-560/month (depends on usage)

## Roadmap

### Completed (MVP)
- [x] Database models & relationships
- [x] OpenAI integration with retry logic
- [x] Psychology analysis engines
- [x] Therapy database (8 modalities)
- [x] REST API (all CRUD operations)
- [x] Timeline visualization
- [x] Beautiful frontend interface

### In Progress
- [ ] User authentication
- [ ] Data export (PDF/CSV)
- [ ] Comparison tools
- [ ] Advanced visualizations

### Future
- [ ] Multi-persona support
- [ ] Collaboration features
- [ ] Public persona library
- [ ] Research API
- [ ] Mobile app

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Maintain the earth-tone aesthetic (frontend)
5. Follow existing code patterns
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

**Psychology Research:**
- Attachment Theory (Bowlby, Ainsworth)
- Big Five Personality Model (Costa & McCrae)
- ACE Study (Felitti et al.)
- Developmental Trauma Disorder (van der Kolk)

**Therapeutic Modalities:**
- CBT (Beck, Ellis)
- ACT (Hayes)
- EMDR (Shapiro)
- IFS (Schwartz)
- DBT (Linehan)

**Technology:**
- OpenAI GPT-4o for AI analysis
- FastAPI framework
- Next.js framework
- Tailwind CSS

## Support

- **Documentation**: See `/backend/README.md` and `/frontend/README.md`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## Citation

If you use this in research or education:

```
Persona Evolution Simulator (2025)
AI-powered psychological development modeling
https://github.com/your-username/persona-evolution-simulator
```

---

**Built with care for psychology professionals, researchers, and students.**

*Note: This is a simulation tool for educational and research purposes. It is not a substitute for professional mental health care. If you or someone you know is struggling, please contact a licensed mental health professional.*
