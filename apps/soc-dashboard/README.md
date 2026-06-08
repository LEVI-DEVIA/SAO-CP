# SAO-CP SOC Dashboard

This is the Next.js frontend for the Security Operations Center (SOC). It is designed to be used by human security analysts.

## Features
- Real-time display of alerts received from the SAO-CP Agent via the FastAPI backend (using WebSockets).
- Allows analysts to review the AI's reasoning and proposed actions.
- Provides a one-click validation mechanism (Approve/Reject) for the AI's proposals.

## How to run

We recommend using the root `Makefile` (`make run-soc-dashboard`). 

If you want to run it manually:

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).
