import { NextResponse } from 'next/server';

export async function POST(request) {
  const logEvent = await request.json();
  
  const splunkPayload = {
    time: new Date().getTime() / 1000,
    host: "critical-health-app",
    source: "frontend-actions",
    sourcetype: "_json",
    event: logEvent
  };

  try {
    const splunkResponse = await fetch(process.env.NEXT_PUBLIC_SPLUNK_HEC_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Splunk ${process.env.SPLUNK_HEC_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(splunkPayload)
    });

    if (!splunkResponse.ok) {
      throw new Error(`Splunk HEC Error: ${splunkResponse.statusText}`);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Failed to send log to Splunk:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}