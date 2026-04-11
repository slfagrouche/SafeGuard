# Contributing to SafeGuard

Thanks for your interest in contributing. SafeGuard is a crisis monitoring platform built to help people in conflict zones and disaster areas. Every contribution matters.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Follow the setup instructions in [README.md](README.md)

## Development Setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with your local values
uvicorn server:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.example .env
npm start
```

## Pull Request Process

1. Create a feature branch from `main`
2. Write clear commit messages in imperative form ("Add feature", not "Added feature")
3. Include tests for new functionality
4. Update documentation if you change APIs
5. Open a PR with a clear description of what and why

## Code Style

- **Python**: Follow PEP 8, use type hints, format with Ruff
- **JavaScript/React**: ESLint + Prettier, functional components with hooks
- **Commits**: One logical change per commit

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce
- Include browser/OS info for frontend bugs
- Include logs or error messages

## Security

If you find a security vulnerability, **do not open a public issue**. Email the maintainer directly.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
