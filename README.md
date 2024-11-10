# Confluence Questions to Discourse Migrator

A Python tool designed to migrate a Confluence questions based Q&A site and their associated content (answers, comments, and attachments) to a Discourse forum.
The tool has been generated using AI, and is based on the migrator_specification.md file.

## Features

- Migrates questions with full content preservation
- Handles attachments and images
- Handles question and answer comments by formatting them as Discourse expandable quotes
- Preserves original authorship information by mentioning users by their display name
- Does NOT migrate users, but registers them in a file called 'user_registry.csv'
- Maintains question timestamps
- Supports both bulk migration and single question migration
- Includes dry-run capability for testing
- Tracks migrated questions to prevent duplicates (in target/migrated_questions.json)
- Preserves question topics as Discourse tags
- Handles HTML to Markdown conversion

## Content Conversions

During migration, the following conversions are automatically applied:

- **Text Formatting**
  - Confluence wiki markup → Markdown
  - HTML → Markdown
  - Code blocks with syntax highlighting
  - Tables
  
- **Media & Attachments**
  - Images → Uploaded and embedded in Discourse
  - File attachments → Uploaded and linked
  - Video embeds → Compatible Discourse embeds

- **Metadata**
  - Question labels → Discourse tags
  - User mentions → Discourse @mentions
  - Internal links → Updated Discourse URLs
  - Timestamps → Preserved in Discourse format
  
- **Special Elements**
  - Info/warning/note macros → Discourse quotes/notices
  - Emoticons → Emoji equivalents
  

## Prerequisites

- Python 3.x
- Access to both Confluence and Discourse instances
- Required API credentials for both platforms
- Confluence questions installed and licensed

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd confluence-to-discourse-migrator
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```env
CONFLUENCE_URL=<https://your-confluence-instance>
CONFLUENCE_USERNAME=<your user name>
CONFLUENCE_PASSWORD=<your confluence password>>
CONFLUENCE_API_TOKEN=your-confluence-api-token

DISCOURSE_URL=<https://your-discourse-instance>
DISCOURSE_API_KEY=<your-discourse-api-key>

# use system user for Discourse
DISCOURSE_API_USERNAME=system

# Confluence space key - which is optional
CONFLUENCE_SPACE_KEY=

```

4. Run the migrator:
```bash
python3 QuestionMigrator.py
```

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner

## Usage

### Basic Usage

Run a dry migration to test (no actual changes):
```bash
python QuestionMigrator.py --dry-run
```

Perform actual migration:
```bash
python QuestionMigrator.py --do-run
```

### Additional Options

Migrate a specific number of questions:
```bash
python QuestionMigrator.py --try-count 5
```

Migrate a single question by ID:
```bash
python QuestionMigrator.py --question-id "12345"
```

Force migration even for previously migrated questions:
```bash
python QuestionMigrator.py --ignore-duplicate
```

Delete all migrated topics (use with caution):
```bash
python QuestionMigrator.py --delete-all-topics
```

## Project Structure

The project consists of several key components:

- `QuestionMigrator.py`: Main migration logic
- `ConfluenceQuestionsFetcher.py`: Handles Confluence API interactions
- `DiscourseClient.py`: Manages Discourse API interactions
- `UserRegistry.py`: Tracks user mappings between platforms
- `logger_config.py`: Logging configuration

## Development Notes

To recreate this project, you would need to implement:

1. `ConfluenceQuestionsFetcher.py`:
   - Methods for fetching questions, answers, and comments from Confluence
   - Authentication handling
   - Pagination support

2. `DiscourseClient.py`:
   - Topic and post creation
   - File upload functionality
   - Category management
   - Authentication handling

3. `UserRegistry.py`:
   - User mapping between Confluence and Discourse
   - User data storage and retrieval

4. `logger_config.py`:
   - Logging setup and configuration


Also checkout the migrator_specification.md which contains the prompts used to generate this project.


## Error Handling

The migrator includes comprehensive error handling for:
- Missing environment variables
- API failures
- Network issues
- File upload problems
- Authentication errors

## Limitations

- Cannot automatically mark answers as solutions in Discourse
- Attachment handling may require manual verification
- User mentions and internal links may need manual updating
- Rate limiting may affect migration speed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

Copyright (c) [2024] [Francis Martens]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.