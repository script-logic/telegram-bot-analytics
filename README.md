# 🤖 Google Sheets LLM Analyzer

Professional data analysis system for Google Sheets with LLM integration for processing text entries via API.

## ✨ Features

- 📊 **Data analysis** from Google Sheets with categorization support
- 🔗 **Google Sheets integration** via API
- 🤖 **AI analysis** of text entries via OpenRouter/OpenAI
- 🐳 **Ready Docker image** for quick deployment
- 🔐 **Secure credentials storage** in Base64 format
- ⚙️ **Type-safe configuration** via Pydantic v2

## 🚀 Quick Start

### 1. 📦 Installation with Poetry

#### 1.1 Prerequisites
- Python 3.11 or higher
- [Poetry](https://python-poetry.org/) installed globally
- Google Cloud Project with Sheets API enabled
- (Optional) OpenRouter API key for LLM features

#### 1.2 Installation Steps
```bash
# Clone repository
git clone https://github.com/script-logic/google-sheets-llm-analyzer.git
cd google-sheets-llm-analyzer

# Install dependencies
poetry install

# Copy environment configuration
cp .env.example .env

# Edit .env file with your credentials
```

### 2. Google Sheets API Setup

#### 2.1 Creating Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project in Google Cloud or select an existing one
3. Enable **Google Sheets API** for the project
4. Create a Service Account and download the JSON key
5. Grant access to your Google Sheet for the email from the JSON file

#### 2.2 Encoding Credentials to Base64
For convenience and additional security, we store the JSON key not as a separate JSON file but in base64 format in the .env file
```bash
# Use the provided script to encode service-account.json
python scripts/encode_credentials.py path/to/service-account.json

# Copy the output to the .env file
# GOOGLE_CREDENTIALS_BASE64=eyJ0eXBlIjoic2V...
```

#### 2.3 Getting Spreadsheet ID and Sheet Name
- Your spreadsheet URL: `https://docs.google.com/spreadsheets/d/YOUR_ID/edit`
- Copy the part between `/d/` and `/edit`
- Specify in `.env`: `SPREADSHEET_ID=your_spreadsheet_id_here`
- Open the spreadsheet in a browser and copy the sheet name from the bottom left
- Specify in `.env`: `SHEET_NAME=sheet_name_in_spreadsheet`

### 3. OpenRouter Setup (Optional)
1. Get an API key at [OpenRouter](https://openrouter.ai/)
2. Specify in `.env`: `OPENROUTER_API_KEY=your_api_key_here`
3. Choose a model, the free `mistralai/devstral-2512:free` is used by default

## 💻 Usage

### Basic Commands
```bash
# Analysis via Google Sheets API
poetry run python main.py --api

# Analysis via Google Sheets API + LLM analysis
poetry run python main.py --api --llm

# Analysis from CSV file
poetry run python main.py --csv data.csv

# Connection test only
poetry run python main.py --api --test
```

### Command Line Parameters

| Parameter | Description |
|-----------|-------------|
| `--api` | Use Google Sheets API |
| `--csv <file>` | Use CSV file |
| `--llm` | Enable LLM analysis |
| `--test` | Connection test only |
| `--raw` | Show raw data |
| `--debug` | Debug mode |

### Sample Output

```
poetry run python main.py --api --llm --raw --debug
```

```
✅ Config loaded from .env
   Spreadsheet: 1TIKSAwTuIgsHvNoZGlZi6Pr8_mRtRpB1sEzxoh10V-8
   Service Email: telegrambot@telegram-bot-analytics.iam.gserviceaccount.com
╭────────────────────────────────────────────────────────────────────────────╮
│                                                                            │
╰─ 📊 Google Sheets LLM Analyzer 🔗 Google Sheets Integration 💡 Analys... ─╯
╭──────────────────────╮
│ System Configuration │
╰──────────────────────╯
 Google Sheet     1TIKSAwTuIgsHvNoZGlZi6Pr8_mRtRpB1sEzxoh10V-8
 Sheet            Sheetj1
 Category column  Column 3
 LLM key          Provided
 Debug mode       Yes

✅ Loaded 7 rows from Google Sheet
⠴ ✅ Data loaded
╭───────────────────╮
│📄 Raw Data        │
╰───────────────────╯
0: ['Request ID', 'Date and Time', 'Category', 'Choice', 'Processing Date', 'Status']
1: ['1', '15.01.2026 8:06:16', 'Tech Support', 'Why are io requests not asynchronous?', '15.01.2026', 'New']
2: ['2', '16.01.2026 0:31:32', 'Consultation', 'What is error with code 401', '16.01.2026', 'New']
3: ['3', '16.01.2026 0:31:41', 'Tech Support', 'How to get JSON file for Service Account', '16.01.2026', 'New']
4: ['4', '16.01.2026 0:32:49', 'Consultation', 'Why is the code so messy?', '16.01.2026', 'New']
5: ['5', '16.01.2026 1:22:57', 'Consultation', 'Why doesn't the code use FastAPI?', '16.01.2026', 'New']
6: ['6', '16.01.2026 4:17:59', 'Consultation', 'Why is the code so poorly typed?', '16.01.2026', 'New']

⚠️  Skipped 0 rows without category
✅ Found 6 requests with description for LLM analysis
🤖 Starting analysis of 6 requests via LLM...
Analyzing next request...
Analyzing next request...
Analyzing next request...
Analyzing next request...
Analyzing next request...
Analyzing next request...
✅ Analyzed 6 out of 6 requests

╭───────────────────────╮
│ 📈 Request Statistics │
╰───────────────────────╯
╭──────────────┬────────────┬─────────╮
│ Category     │ Count      │ Percent │
├──────────────┼────────────┼─────────┤
│ Consultation │          4 │   66.7% │
│ Tech Support │          2 │   33.3% │
╰──────────────┴────────────┴─────────╯

╭──────────────────────────────────────────────────────────────╮
│  Total requests              6                               │
│  Unique categories           2                               │
│  Most popular category      Consultation (4 requests, 66.7%) │
╰──────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────╮
│🤖 LLM Analysis                                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
🟡  Request #2 (ID: 1)
  Category        Tech Support
  Date            15.01.2026 8:06:16
  Choice          Why are io requests not asynchronous?
  Priority        MEDIUM
  Analysis time   5.01 sec
   📝 Summary: User asks why I/O requests are not executed asynchronously.
   💡 Recommendation: Clarify context: which specific system or library is used, and in which case synchronous I/O execution is observed. Provide code example or logs for further analysis.

🟢  Request #3 (ID: 2)
  Category        Consultation
  Date            16.01.2026 0:31:32
  Choice          What is error with code 401
  Priority        LOW
  Analysis time   2.37 sec
   📝 Summary: User requests information about the meaning of error code 401.
   💡 Recommendation: Provide the user with a brief explanation that error 401 indicates lack of authorization, and offer a link to documentation or troubleshooting guide.

🟢  Request #4 (ID: 3)
  Category        Tech Support
  Date            16.01.2026 0:31:41
  Choice          How to get JSON file for Service Account
  Priority        LOW
  Analysis time   2.69 sec
   📝 Summary: User requests information on obtaining JSON file for Service Account.
   💡 Recommendation: Provide the user with instructions or link to documentation on creating and obtaining JSON file for Service Account. For example, specify steps in Google Cloud Console: 'IAM & Admin' -> 'Service Accounts' -> 'Create Service Account' -> 'Create Key' -> 'JSON'.

🟢  Request #5 (ID: 4)
  Category        Consultation
  Date            16.01.2026 0:32:49
  Choice          Why is the code so messy?
  Priority        LOW
  Analysis time   2.08 sec
   📝 Summary: User requests consultation regarding code quality.
   💡 Recommendation: Ask the user which specific code raises questions, and provide detailed answer or direct to relevant documentation.

🟢  Request #6 (ID: 5)
  Category        Consultation
  Date            16.01.2026 1:22:57
  Choice          Why doesn't the code use FastAPI?
  Priority        LOW
  Analysis time   1.83 sec
   📝 Summary: User asks why the code doesn't use FastAPI.
   💡 Recommendation: Provide information about reasons for choosing alternative framework or suggest documentation on FastAPI integration if possible.

🟢  Request #7 (ID: 6)
  Category        Consultation
  Date            16.01.2026 4:17:59
  Priority        LOW
  Analysis time   2.93 sec
   📝 Summary: User requests consultation regarding poor typing in code.
   💡 Recommendation: Provide the user with documentation or examples of proper typing in code, as well as suggest tools for analyzing and improving typing.

Total analyzed requests: 6
╭─────────────────────────────────────╮
│ ✅ Analysis completed successfully! │
│ Processed requests: 6               │
│ LLM analysis:✅ Enabled             │
╰─────────────────────────────────────╯
```

## 🐳 Docker

### Build Image
```bash
docker build -t google-sheets-llm-analyzer .
```

### Run Container
```bash
# 1. Basic run (uses Google Sheets API)
docker run --rm -t --env-file .env google-sheets-llm-analyzer

# 2. With LLM analysis
docker run --rm -t --env-file .env google-sheets-llm-analyzer python main.py --api --llm

# 3. Connection test only
docker run --rm -t --env-file .env google-sheets-llm-analyzer python main.py --api --test

# 4. With custom environment variables
docker run --rm -t -e SPREADSHEET_ID="your_spreadsheet_id_here" -e GOOGLE_CREDENTIALS_BASE64="your_base64_encoded_json_here" google-sheets-llm-analyzer

# 5. Analyze local CSV file
docker run --rm -t -v "$(pwd)/data.csv:/app/mock_data.csv" google-sheets-llm-analyzer python main.py --csv mock_data.csv

# 6. Interactive mode for debugging
docker run -it --rm --env-file .env google-sheets-llm-analyzer /bin/sh

# 7. Run with debugging
docker run --rm -t --env-file .env google-sheets-llm-analyzer python main.py --api --llm --raw --debug
```

## 🔧 Development

### Development Installation
```bash
# Install project with development dependencies
poetry install

# Activate virtual environment
poetry shell

# OR run commands directly without activation
poetry run python main.py --api
```

### Code Formatting
```bash
# Format code and check
poetry run ruff format .
poetry run ruff check .

# Type checking
poetry run mypy .

# OR run all checks at once
poetry run ruff check --fix .
poetry run mypy .
```

## 📁 Project Structure
```
google_sheets_llm_analyzer/              
├── main.py                              # Main script
├── google_sheets_llm_analyzer_package/  # Source code
│   ├── __init__.py                      # Package file
│   ├── config.py                # Configuration with Pydantic
│   ├── console_printer.py       # Fine formatted console output
│   ├── google_sheets_client.py  # Google Sheets client
│   ├── data_analyzer.py         # Data analysis
│   └── llm_processor.py         # LLM integration
├── scripts/                     # Utility scripts
│   └── encode_credentials.py    # Script for encoding JSON to base64
├── Dockerfile                   # Docker configuration
├── pyproject.toml               # Poetry configuration and dependencies
├── poetry.lock                  # Locked dependencies (generated by Poetry)
└── .env.example                 # Environment variables template
```

## 🔐 Security

- All secrets stored in `.env`
- Service Accounts with minimal privileges used
- API keys can be easily replaced

## 🐛 Troubleshooting

### Google Sheets Access Error
```
✗ Connection error: <HttpError 403>
```
**Solution:** Ensure that:
1. Service Account has access to the spreadsheet
2. GOOGLE_CREDENTIALS_BASE64 is correctly encoded
3. SPREADSHEET_ID is specified correctly

### LLM Error
```
✗ LLM connection error: Incorrect API key
```
**Solution:** Check OPENROUTER_API_KEY in .env

### Empty Data
```
No data for analysis
```
**Solution:** Check that spreadsheet contains data and SHEET_NAME is specified correctly

## 📝 License

MIT License