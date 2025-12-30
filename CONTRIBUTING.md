"""Contributing to Context IQ

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/aishaq13/Context_IQ.git
cd Context_IQ
```

2. Start the development environment:
```bash
docker-compose up -d
```

3. Seed the database with test data:
```bash
docker-compose exec backend python seed_data.py
docker-compose exec backend python compute_recommendations.py
```

4. Run tests:
```bash
docker-compose exec backend pytest
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Max line length: 100 characters
- Format with `black`

### JavaScript/React
- Use ES6+ syntax
- Functional components with hooks
- File naming: PascalCase for components, camelCase for utilities
- Prettier formatting

## Git Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit with descriptive messages:
```bash
git commit -m "feat: add new recommendation algorithm"
```

Commit message format:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for code refactoring
- `test:` for tests
- `docs:` for documentation
- `perf:` for performance improvements
- `chore:` for maintenance tasks

3. Push and create a pull request:
```bash
git push origin feature/your-feature-name
```

## Testing

- Backend: Unit tests with pytest
- Frontend: Component tests with Jest/React Testing Library
- Integration: Docker-based E2E tests

Run tests before submitting PR:
```bash
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

## Pull Request Process

1. Update documentation if needed
2. Ensure all tests pass
3. Provide a clear description of changes
4. Link any related issues
5. Request review from maintainers

## Reporting Issues

Include:
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Docker version, etc.)
- Relevant logs or screenshots
"""
