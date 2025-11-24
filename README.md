# Multimodal Agentic System for A/B Outcome Prediction

**Authors**: Anni Zimina & Orkhan Javadli  
**Institution**: Stanford Graduate School of Business  
**Course**: GSBGEN 390 - Fall 2025  
**Faculty Advisor**: Professor Yu Ding

## Overview

This system predicts A/B testing outcomes BEFORE deployment using multimodal AI.

## Features

- **Individual Virality Scoring**: Score any content (0-100)
- **A/B Winner Prediction**: Compare two variants
- **Multimodal Support**: Text + Images + Videos
- **Real-time Analysis**: 15-second predictions

## Technology Stack (November 2025)

- GPT-5.1 (OpenAI)
- Claude 4 Opus (Anthropic)
- Gemini 3 Pro Preview (Google)

## Installation

```bash
pip install flask openai anthropic google-generativeai pillow numpy
```

## Usage

```bash
python app.py
```

Access at: http://localhost:8080

## Research

Based on pilot study with 25 SMB restaurants:
- 68% alignment with human preferences
- 72% alignment with online engagement
- 94% cost reduction vs traditional A/B testing

## Citation

Zimina, A., & Javadli, O. (2025). Multimodal Agentic Systems for A/B Outcome Prediction of Content. Stanford GSB GSBGEN 390 Research Project.
