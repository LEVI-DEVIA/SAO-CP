# SAO-CP Health App

This is a Next.js frontend simulating a medical platform for a university hospital (CHU). It serves as the target application that generates interaction logs.

## Features
- Simulates user interactions with medical records.
- Logs events which are then captured by Splunk to be monitored by the SAO-CP ecosystem.

## How to run

We recommend using the root `Makefile` (`make run-health-app`). 

If you want to run it manually:

1. Install dependencies:
```bash
npm install
```

2. Run the development server (we recommend using port 3001 to avoid conflicts with the SOC dashboard):
```bash
PORT=3001 npm run dev
```

The app will be available at [http://localhost:3001](http://localhost:3001).
