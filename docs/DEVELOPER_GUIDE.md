# Developer Guide

## Architecture

```
┌─────────────────────────────────────────────┐
│              React Frontend (src/)           │
│  Pages → Components → Services → Tauri API   │
└─────────────────────┬───────────────────────┘
                      │ invoke()
┌─────────────────────▼───────────────────────┐
│           Tauri Backend (src-tauri/)         │
│  ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │ Scanner │ │ Repairs │ │ AI / OpenAI  │  │
│  └─────────┘ └─────────┘ └──────────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │ SQLite  │ │  PDF    │ │  Licensing   │  │
│  └─────────┘ └─────────┘ └──────────────┘  │
└─────────────────────────────────────────────┘
```

## Adding a Tauri Command

1. Implement the function in the appropriate Rust module
2. Register in `src-tauri/src/lib.rs` invoke_handler
3. Add TypeScript types in `src/services/types.ts`
4. Add API wrapper in `src/services/tauri.ts`
5. Add mock handler in `src/services/mock.ts` for web preview

## Adding a Page

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/layout/AppLayout.tsx`

## Database Schema

See `src/database/schema.md` for table definitions.

## AI Provider Abstraction

The AI module supports multiple providers via configuration:

- `ai_provider` setting (default: `openai`)
- `ai_base_url` for custom endpoints (Azure OpenAI, etc.)
- `ai_model` for model selection

To add a new provider, extend `src-tauri/src/ai/mod.rs`.

## System Scanner

Uses the `sysinfo` crate for cross-platform system information. Platform-specific enhancements go in `src-tauri/src/scanner/mod.rs`.

## Testing

```bash
npm run test           # Vitest frontend tests
cd src-tauri && cargo test  # Rust unit tests
```

## Code Conventions

- React: Functional components, hooks, Zustand for global state
- Rust: Module per domain, `thiserror` for errors, serde for serialization
- Styling: Tailwind utility classes, dark theme tokens in `tailwind.config.js`

## Build Pipeline

1. `npm run build` — Vite builds React to `dist/`
2. `tauri build` — Rust compiles and bundles with WebView
3. Installers generated in `src-tauri/target/release/bundle/`
