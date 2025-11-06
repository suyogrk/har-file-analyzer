# har-file-analyzer

A Streamlit application to analyze HAR (HTTP Archive) files for network request inspection, performance metrics, and visualization.

## Project Overview

har-file-analyzer allows users to upload HAR files and interactively analyze the network requests captured during web browsing or API interactions. The app extracts key metrics, identifies performance bottlenecks, and provides graphical insights using charts and filters.

## Live Demo

The application is hosted and accessible at:  
[https://har-file-analyzer.streamlit.app/](https://har-file-analyzer.streamlit.app/)

## Features

- Upload and parse HAR files from browsers or tools
- View detailed network request tables and filter by criteria
- Visualize request counts, durations, and other metrics using interactive charts
- Analyze timing breakdown for performance optimization insights

## Installation

Ensure Python 3.8+ is installed. Install dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app locally:

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

Alternatively, use the hosted version linked above for quick access.

## Requirements

All required Python libraries are listed in `requirements.txt`.

## Contributing

Contributions and suggestions are welcome. Please open an issue or create a pull request.

## License

MIT License

Copyright (c) 2025 [Your Name or Organization]

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