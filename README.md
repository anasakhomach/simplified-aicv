# AI CV Generator

A Streamlit application that generates tailored CVs using AI, built with LangChain and Google's Gemini AI.

## Features

- Upload your existing CV
- Paste job descriptions
- AI-powered CV tailoring
- Interactive review and editing
- Professional CV generation

## Local Development

### Prerequisites

- Python 3.8+
- Google AI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/anasakhomach/simplified-aicv.git
cd simplified-aicv
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.streamlit/secrets.toml` and add your Google AI API key
   - Or set `GOOGLE_API_KEY` environment variable

4. Run the application:
```bash
streamlit run app.py
```

## Deployment on Streamlit Community Cloud

### Quick Deploy

1. **Fork this repository** to your GitHub account
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Click "New app"**
4. **Connect your GitHub account** if not already connected
5. **Select your forked repository**
6. **Set the main file path** to `app.py`
7. **Add your secrets**:
   - Go to "Advanced settings"
   - Add `GOOGLE_API_KEY` with your Google AI API key
8. **Click "Deploy"**

### Manual Setup

1. **Create GitHub Repository**:
   ```bash
   # If you haven't already
   git remote add origin https://github.com/YOUR_USERNAME/simplified-aicv.git
   git push -u origin main
   ```

2. **Configure Secrets**:
   - In Streamlit Community Cloud, go to your app settings
   - Navigate to "Secrets"
   - Add the following:
   ```toml
   GOOGLE_API_KEY = "your_actual_google_api_key_here"
   ```

3. **Deploy**:
   - Your app will automatically deploy when you push to the main branch
   - URL format: `https://YOUR_USERNAME-simplified-aicv-app-HASH.streamlit.app`

## Getting Google AI API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and add it to your secrets configuration

## Project Structure

```
├── app.py              # Main Streamlit application
├── state.py            # Application state management
├── models.py           # Pydantic data models
├── chains.py           # LangChain AI chains
├── nodes.py            # Processing nodes
├── graph.py            # Application workflow graph
├── requirements.txt    # Python dependencies
├── .streamlit/
│   ├── config.toml     # Streamlit configuration
│   └── secrets.toml    # Secrets template (not committed)
└── .github/workflows/
    └── ci.yml          # CI/CD pipeline
```

## Architecture

This application follows a strict architectural pattern:

- **Single Application Focus**: Built for CV generation, not as a framework
- **Six-File Limit**: Core logic contained in 6 Python files
- **Unidirectional Data Flow**: State flows through app.py → graph → nodes → chains
- **Pure Functions**: Nodes are stateless, chains handle AI generation
- **Human-in-the-Loop**: Interactive review at key stages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details