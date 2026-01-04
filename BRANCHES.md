# Development Branches Overview

## Current Branches

### `main` (Production)
- **Status**: ✅ Stable production branch
- **Purpose**: Production-ready code that has been tested
- **Use**: For end users and production deployments

### `develop-ai` (AI Development)
- **Status**: 🚀 Active development
- **Purpose**: Development of AI chat features
- **Focus Areas**:
  - 💬 Chat interface improvements
  - 🔧 Model backend enhancements
  - ⚡ Streaming optimizations
  - 📝 Conversation management
  - 🎨 UI/UX improvements
- **Switch to this branch**: `git checkout develop-ai`

### `develop-video` (Video Development)
- **Status**: 🎬 Active development
- **Purpose**: Development of text-to-video features
- **Focus Areas**:
  - 🎥 Video generation backends (Sora 2, Runway, Pika)
  - 🔌 Video generation API
  - 🎞️ Video gallery and management
  - ⚙️ Video settings and customization
  - 🆕 New video backend implementations
- **Switch to this branch**: `git checkout develop-video`

## Quick Reference

```bash
# View all branches
git branch -a

# Switch to AI development
git checkout develop-ai

# Switch to video development
git checkout develop-video

# Switch back to main
git checkout main

# Create feature branch from development branch
git checkout -b feature/my-feature develop-ai
```

## Branch Strategy

```
Feature Development Flow:
1. Create feature branch from develop-ai or develop-video
2. Develop and test feature
3. Merge feature branch to development branch
4. Test on development branch
5. Merge development branch to main when ready
```

For detailed development guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md).

