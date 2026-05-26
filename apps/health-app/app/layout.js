import './globals.css';

export const metadata = {
  title: 'CHU Medical Platform',
  description: 'Target application for Splunk Agentic Ops',
};

export default function RootLayout({ children }) {
  return (
    <html lang="fr">
      <body style={{ margin: 0, fontFamily: 'sans-serif', backgroundColor: '#f0f4f8' }}>
        {children}
      </body>
    </html>
  );
}