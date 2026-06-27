# Contributing to Thorpe

Thank you for your interest in contributing to Thorpe!

## Development Setup

1. Fork the repository
2. Clone your fork
3. Install prerequisites (Node.js, Rust, Tauri dependencies)
4. Run `npm install`
5. Run `bash scripts/generate-icons.sh`
6. Start development: `npm run tauri:dev`

## Code Style

- **TypeScript**: Strict mode, functional React components
- **Rust**: Standard rustfmt formatting
- **CSS**: Tailwind utility classes, dark theme
- Match existing patterns and naming conventions

## Pull Request Process

1. Create a feature branch from `main`
2. Write clear commit messages
3. Add tests for new functionality
4. Ensure `npm run test` and `npm run lint` pass
5. Update documentation if needed
6. Submit a pull request with a clear description

## Testing

```bash
npm run test          # Frontend tests
bash scripts/test.sh  # Full test suite
```

## Security

- Never commit API keys or credentials
- Follow the security guidelines in SECURITY.md
- Report vulnerabilities to security@thorpe.app

## Areas for Contribution

- Platform-specific diagnostic improvements
- Additional knowledge base articles
- UI/UX enhancements
- Accessibility improvements
- Internationalization (i18n)
- Additional AI provider integrations
