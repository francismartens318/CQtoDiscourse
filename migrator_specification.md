# Confluence Questions to Discourse Migrator Specification

## Overview

This document contains the prompts and specifications needed to recreate a tool that migrates questions from Confluence's Questions feature to a Discourse forum.

## Core Components

### 1. Question Migrator Class

**Prompt**: Create a QuestionMigrator class that handles the migration of questions from Confluence to Discourse. It should:
- Initialize with configuration from environment variables
- Support dry run mode
- Track migrated questions
- Handle both bulk and single question migration
- Process questions in chronological order
- Support resuming interrupted migrations

### 2. Confluence Questions Fetcher

**Prompt**: Create a ConfluenceQuestionsFetcher class that handles all interactions with the Confluence API. It should:
- Fetch questions with pagination
- Get question details
- Get answers and comments
- Support space key filtering
- Handle authentication
- Sort questions by creation date

### 3. Discourse Client

**Prompt**: Create a DiscourseClient class that manages all interactions with the Discourse API. Requirements:
- Create topics and posts
- Upload attachments
- Handle categories and tags
- Support topic deletion
- Manage solutions
- Handle rate limiting

### 4. Content Processing Components

#### 4.1 Answer Processor

**Prompt**: Create an AnswerProcessor class that handles the processing and migration of answers. It should:
- Process answer content
- Handle attachments
- Register answer authors
- Mark accepted solutions
- Preserve answer chronology
- Format answer metadata

#### 4.2 Attachment Processor

**Prompt**: Create an AttachmentProcessor class that handles file attachments. Requirements:
- Download attachments from Confluence
- Upload to Discourse
- Handle image conversions
- Support allowed file types
- Process inline images
- Maintain attachment references

#### 4.3 Content Formatter

**Prompt**: Create a ContentFormatter class that handles content conversion. It should:
- Convert HTML to Markdown
- Process internal links
- Handle emojis
- Format question and answer content
- Add migration metadata
- Preserve formatting and structure

### 5. User Management

**Prompt**: Create a UserRegistry class to track user mappings between platforms. Requirements:
- Register users from questions, answers, and comments
- Store user mappings
- Handle user lookup
- Export user data
- Support user anonymization

### 6. Category Management

**Prompt**: Create a DiscourseCategoryManager class to handle Discourse categories. It should:
- Create required categories
- Map questions to categories
- Handle category slugs
- Support category lookup
- Manage category permissions

### 7. Tag Management

**Prompt**: Create a DiscourseTagManager class to handle tags. Requirements:
- Clean tag names
- Create tags
- Add tags to topics
- Handle tag limitations
- Support tag hierarchies

## Configuration

**Prompt**: Create a configuration setup that includes:
- Environment variables for credentials
- Logging configuration
- Debug settings
- VSCode launch configurations
- Migration parameters

## Command Line Interface

**Prompt**: Create a CLI interface with the following options:
- Dry run mode
- Single question migration
- Bulk migration
- Try count limitation
- Delete all topics
- Space key filtering
- Resume functionality

## Error Handling

**Prompt**: Implement comprehensive error handling for:
- API failures
- Network issues
- Authentication errors
- File processing errors
- Rate limiting
- Data validation
- Resource constraints

## Testing

**Prompt**: Create test cases for:
- Content conversion
- API interactions
- Error handling
- User mapping
- File processing
- Migration integrity
- Performance testing

## Documentation

**Prompt**: Create comprehensive documentation including:
- Installation instructions
- Usage examples
- Configuration guide
- Troubleshooting
- API reference
- Migration best practices
- Performance considerations 