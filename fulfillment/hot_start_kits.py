"""
HOT-START KITS: Pre-configured Starter Templates by Pack
========================================================

Accelerate time-to-first-artifact with pre-built templates:
- Boilerplate code/configs per service type
- Common patterns already implemented
- Reduces setup time by 60-80%

Updated: Jan 2026
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class HotStartKit:
    """A hot-start kit for a specific pack/service type"""
    id: str
    pack: str
    name: str
    description: str
    files: Dict[str, str]  # filename -> template content
    dependencies: List[str] = field(default_factory=list)
    setup_commands: List[str] = field(default_factory=list)
    estimated_time_saved_minutes: int = 30
    tags: List[str] = field(default_factory=list)


# Pre-built hot-start kits
HOT_START_KITS: Dict[str, List[HotStartKit]] = {
    'web_dev': [
        HotStartKit(
            id='web_react_starter',
            pack='web_dev',
            name='React + Vite Starter',
            description='Modern React app with Vite, TailwindCSS, and common patterns',
            files={
                'package.json': '''{
  "name": "aigentsy-web-app",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "vite": "^5.0.0"
  }
}''',
                'vite.config.js': '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})''',
                'tailwind.config.js': '''/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
}''',
                'src/App.jsx': '''import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

function Home() {
  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold">Welcome</h1>
      {/* Your content here */}
    </main>
  )
}

export default App''',
            },
            dependencies=['node', 'npm'],
            setup_commands=['npm install', 'npm run dev'],
            estimated_time_saved_minutes=45,
            tags=['react', 'vite', 'tailwind', 'spa'],
        ),
        HotStartKit(
            id='web_nextjs_starter',
            pack='web_dev',
            name='Next.js Full-Stack Starter',
            description='Next.js 14 with App Router, API routes, and database setup',
            files={
                'package.json': '''{
  "name": "aigentsy-nextjs-app",
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}''',
                'app/page.tsx': '''export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-24">
      <h1 className="text-4xl font-bold">Welcome</h1>
    </main>
  )
}''',
                'app/api/hello/route.ts': '''import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({ message: 'Hello from API' })
}''',
            },
            dependencies=['node', 'npm'],
            setup_commands=['npm install', 'npm run dev'],
            estimated_time_saved_minutes=60,
            tags=['nextjs', 'fullstack', 'typescript', 'api'],
        ),
    ],
    'mobile_dev': [
        HotStartKit(
            id='mobile_react_native',
            pack='mobile_dev',
            name='React Native Expo Starter',
            description='Cross-platform mobile app with Expo and common patterns',
            files={
                'package.json': '''{
  "name": "aigentsy-mobile-app",
  "version": "1.0.0",
  "main": "node_modules/expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios"
  },
  "dependencies": {
    "expo": "~49.0.0",
    "expo-status-bar": "~1.6.0",
    "react": "18.2.0",
    "react-native": "0.72.6",
    "@react-navigation/native": "^6.1.9"
  }
}''',
                'App.js': '''import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';

export default function App() {
  return (
    <NavigationContainer>
      <View style={styles.container}>
        <Text style={styles.title}>Welcome</Text>
        <StatusBar style="auto" />
      </View>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
});''',
            },
            dependencies=['node', 'expo-cli'],
            setup_commands=['npm install', 'expo start'],
            estimated_time_saved_minutes=40,
            tags=['react-native', 'expo', 'cross-platform'],
        ),
        HotStartKit(
            id='mobile_flutter',
            pack='mobile_dev',
            name='Flutter Starter',
            description='Flutter app with Material Design and common widgets',
            files={
                'pubspec.yaml': '''name: aigentsy_app
description: A new Flutter project.
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2

flutter:
  uses-material-design: true''',
                'lib/main.dart': '''import 'package:flutter/material.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Aigentsy App',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Welcome')),
      body: const Center(
        child: Text('Hello, World!', style: TextStyle(fontSize: 24)),
      ),
    );
  }
}''',
            },
            dependencies=['flutter'],
            setup_commands=['flutter pub get', 'flutter run'],
            estimated_time_saved_minutes=35,
            tags=['flutter', 'dart', 'material-design'],
        ),
    ],
    'devops': [
        HotStartKit(
            id='devops_docker_compose',
            pack='devops',
            name='Docker Compose Stack',
            description='Multi-service Docker setup with common patterns',
            files={
                'docker-compose.yml': '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:''',
                'Dockerfile': '''FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000
CMD ["npm", "start"]''',
                '.dockerignore': '''node_modules
.git
.env
*.log''',
            },
            dependencies=['docker', 'docker-compose'],
            setup_commands=['docker-compose up -d'],
            estimated_time_saved_minutes=50,
            tags=['docker', 'compose', 'postgres', 'redis'],
        ),
        HotStartKit(
            id='devops_k8s_starter',
            pack='devops',
            name='Kubernetes Manifests',
            description='K8s deployment, service, and ingress configs',
            files={
                'k8s/deployment.yaml': '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: app:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"''',
                'k8s/service.yaml': '''apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  type: ClusterIP
  selector:
    app: app
  ports:
  - port: 80
    targetPort: 3000''',
                'k8s/ingress.yaml': '''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app
            port:
              number: 80''',
            },
            dependencies=['kubectl'],
            setup_commands=['kubectl apply -f k8s/'],
            estimated_time_saved_minutes=45,
            tags=['kubernetes', 'k8s', 'deployment'],
        ),
    ],
    'content': [
        HotStartKit(
            id='content_blog_post',
            pack='content',
            name='Blog Post Template',
            description='SEO-optimized blog post structure',
            files={
                'blog_template.md': '''# [Title: Include Primary Keyword]

**Meta Description:** [150-160 characters summarizing the post]

**Target Keywords:** [primary], [secondary], [long-tail]

---

## Introduction
[Hook the reader - question, statistic, or bold statement]

[Briefly explain what they'll learn]

---

## [Main Section 1]
[Key point with supporting details]

### [Subsection if needed]
[Detailed explanation]

---

## [Main Section 2]
[Key point with supporting details]

> **Pro Tip:** [Actionable advice]

---

## [Main Section 3]
[Key point with supporting details]

---

## Conclusion
[Summarize key takeaways]

[Call to action]

---

**Related Posts:**
- [Link 1]
- [Link 2]
''',
            },
            dependencies=[],
            setup_commands=[],
            estimated_time_saved_minutes=20,
            tags=['blog', 'seo', 'content-marketing'],
        ),
    ],
    'design': [
        HotStartKit(
            id='design_figma_tokens',
            pack='design',
            name='Design System Tokens',
            description='Standard design tokens for consistent styling',
            files={
                'tokens.json': '''{
  "colors": {
    "primary": {"50": "#eff6ff", "500": "#3b82f6", "900": "#1e3a8a"},
    "gray": {"50": "#f9fafb", "500": "#6b7280", "900": "#111827"},
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444"
  },
  "spacing": {
    "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"
  },
  "typography": {
    "fontFamily": {"sans": "Inter, system-ui, sans-serif"},
    "fontSize": {"xs": "12px", "sm": "14px", "base": "16px", "lg": "18px", "xl": "20px"},
    "fontWeight": {"normal": 400, "medium": 500, "bold": 700}
  },
  "borderRadius": {"sm": "4px", "md": "8px", "lg": "12px", "full": "9999px"},
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.1)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)"
  }
}''',
            },
            dependencies=[],
            setup_commands=[],
            estimated_time_saved_minutes=25,
            tags=['design-system', 'tokens', 'figma'],
        ),
    ],
}


class HotStartKitManager:
    """
    Manage and apply hot-start kits.

    Flow:
    1. Identify service type/pack
    2. Select appropriate kit
    3. Apply kit files to workspace
    4. Run setup commands
    """

    def __init__(self):
        self.kits = HOT_START_KITS
        self.stats = {
            'kits_applied': 0,
            'time_saved_minutes': 0,
            'by_pack': {},
        }

    def get_kits_for_pack(self, pack: str) -> List[HotStartKit]:
        """Get available kits for a pack"""
        return self.kits.get(pack, [])

    def get_kit(self, kit_id: str) -> Optional[HotStartKit]:
        """Get kit by ID"""
        for pack_kits in self.kits.values():
            for kit in pack_kits:
                if kit.id == kit_id:
                    return kit
        return None

    def select_best_kit(
        self,
        pack: str,
        requirements: Dict[str, Any] = None,
    ) -> Optional[HotStartKit]:
        """
        Select best kit based on requirements.

        Args:
            pack: Service pack type
            requirements: Optional requirements to match against

        Returns:
            Best matching kit or first available
        """
        kits = self.get_kits_for_pack(pack)
        if not kits:
            return None

        requirements = requirements or {}

        # Score kits based on tag matches
        def score_kit(kit: HotStartKit) -> int:
            score = 0
            req_tags = requirements.get('tags', [])
            for tag in req_tags:
                if tag.lower() in [t.lower() for t in kit.tags]:
                    score += 10
            return score

        scored = [(score_kit(k), k) for k in kits]
        scored.sort(key=lambda x: x[0], reverse=True)

        return scored[0][1]

    async def apply_kit(
        self,
        kit_id: str,
        workspace_path: str,
    ) -> Dict[str, Any]:
        """
        Apply kit files to workspace.

        Args:
            kit_id: Kit to apply
            workspace_path: Target directory

        Returns:
            Result with files created and commands to run
        """
        kit = self.get_kit(kit_id)
        if not kit:
            return {'ok': False, 'error': 'Kit not found'}

        files_created = []
        for filename, content in kit.files.items():
            files_created.append({
                'path': f"{workspace_path}/{filename}",
                'content': content,
            })

        # Update stats
        self.stats['kits_applied'] += 1
        self.stats['time_saved_minutes'] += kit.estimated_time_saved_minutes
        pack_stats = self.stats['by_pack'].setdefault(kit.pack, {'count': 0, 'time_saved': 0})
        pack_stats['count'] += 1
        pack_stats['time_saved'] += kit.estimated_time_saved_minutes

        logger.info(f"Applied hot-start kit: {kit.name}")

        return {
            'ok': True,
            'kit': kit.name,
            'files_created': files_created,
            'setup_commands': kit.setup_commands,
            'dependencies': kit.dependencies,
            'estimated_time_saved_minutes': kit.estimated_time_saved_minutes,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get manager stats"""
        return {
            **self.stats,
            'total_kits': sum(len(kits) for kits in self.kits.values()),
            'packs_covered': list(self.kits.keys()),
        }

    def list_all_kits(self) -> List[Dict[str, Any]]:
        """List all available kits"""
        all_kits = []
        for pack, kits in self.kits.items():
            for kit in kits:
                all_kits.append({
                    'id': kit.id,
                    'pack': kit.pack,
                    'name': kit.name,
                    'description': kit.description,
                    'tags': kit.tags,
                    'time_saved_minutes': kit.estimated_time_saved_minutes,
                })
        return all_kits


# Singleton
_kit_manager: Optional[HotStartKitManager] = None


def get_hot_start_manager() -> HotStartKitManager:
    """Get or create hot-start kit manager"""
    global _kit_manager
    if _kit_manager is None:
        _kit_manager = HotStartKitManager()
    return _kit_manager
