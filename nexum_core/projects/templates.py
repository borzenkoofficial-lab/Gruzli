from pathlib import Path


REACT_VITE_FILES = {
    "package.json": """{
  "name": "nexum-generated-app",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "echo \"No tests configured\""
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "vite": "^7.0.0",
    "typescript": "^5.0.0"
  }
}""",
    "index.html": """<!doctype html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Nexum App</title></head>
<body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>""",
    "vite.config.ts": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({ plugins: [react()] })
""",
    "src/main.tsx": """import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
function App() { return <main><h1>Nexum Generated App</h1><p>Project runtime is operational.</p></main> }
createRoot(document.getElementById('root')!).render(<App />)
""",
    "src/styles.css": """body { margin: 0; font-family: system-ui, sans-serif; } main { padding: 48px; }"""
}


def create_react_vite_template(root: str) -> list[str]:
    base = Path(root).resolve()
    created = []
    for relative, content in REACT_VITE_FILES.items():
        path = (base / relative).resolve()
        path.relative_to(base)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created.append(relative)
    return created
