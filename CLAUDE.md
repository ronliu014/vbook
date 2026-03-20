# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vbook** (video notebook) is a system for analyzing video content and extracting knowledge into structured documents.

### Core Mission
Transform video content into comprehensive knowledge documents (PPT, mind maps, Markdown summaries) through:
1. Audio extraction with timestamped transcription
2. Content understanding and knowledge outline generation
3. Visual knowledge extraction (screenshots of key graphical information)
4. Integrated document creation with text and images

### Planned Architecture

The system operates in four main stages:

1. **Audio Processing Pipeline**
   - Extract audio from video files
   - Convert speech to text with timestamps
   - Generate timestamped text sequences

2. **Content Analysis Engine**
   - Analyze transcribed text to understand content
   - Generate knowledge outline/hierarchy
   - Build mind map structure

3. **Visual Extraction Module**
   - Identify key video segments based on outline
   - Extract screenshots of graphical information
   - Prioritize visual content with high information density

4. **Document Generation System**
   - Integrate textual and visual knowledge
   - Generate output in multiple formats (PPT, mind map, Markdown)
   - Create cohesive, illustrated documents

## Technology Stack Decisions

Key technology choices to be made:
- Video/audio processing (FFmpeg, MoviePy, etc.)
- Speech-to-text engine (Whisper, Google Cloud Speech, Azure Speech, etc.)
- LLM integration for content understanding
- Mind mapping library
- Document generation framework

## Development Approach

This project is in the initial planning phase. When implementing features:
- Start with a minimal end-to-end prototype before optimizing individual components
- Consider modular design to allow swapping of key components (e.g., different STT engines)
- Plan for handling various video formats and quality levels
- Consider timestamp accuracy for synchronization between audio and visual extraction