# indexer-analyze

This tool analyzes Sonarr's data to provide statistics on which indexers are used to download episode files. It works by iterating through all the series in Sonarr, examining the history of each episode to find out where it was downloaded from, and then tallies the counts for each indexer.

## Features

- Fetches all series from your Sonarr instance.
- Analyzes the history of each episode to determine the source indexer.
- Provides a summary of file counts per indexer.
- Displays results in a clean, formatted table.

## Concurrency

To ensure the analysis is performed as quickly as possible, this tool is built using modern asynchronous Python libraries (`anyio` and `httpx`).

- **Concurrent API Requests:** It makes concurrent requests to the Sonarr API, allowing it to fetch data for multiple series and episodes at the same time.
- **Efficient Processing:** By processing each series in parallel, the tool significantly reduces the total time required to analyze a large Sonarr library compared to a traditional synchronous approach. A configurable semaphore limits the maximum number of simultaneous requests to avoid overwhelming the Sonarr API.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Xevion/indexer-analyze.git
   cd indexer-analyze
   ```

2. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```

## Configuration

Create a `.env` file in the root of the project and add the following environment variables:

```
SONARR_URL=http://your-sonarr-instance:8989
SONARR_API_KEY=your-sonarr-api-key
AUTHELIA_URL=http://your-authelia-instance
AUTHELIA_USERNAME=your-authelia-username
AUTHELIA_PASSWORD=your-authelia-password
```

## Usage

To run the analysis, execute the following command:

```bash
poetry run python main.py
```

The script will then connect to the Sonarr API, process all the series, and output the indexer statistics to the console.

### Example Output

```
Indexer Statistics:
Indexer      | Count
-------------+------
IndexerOne   |  1234
IndexerTwo   |   567
IndexerThree |    89
```
