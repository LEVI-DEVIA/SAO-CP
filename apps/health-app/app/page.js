'use client';

import { useState } from 'react';
import { patients, currentUser } from '../lib/mockData';

export default function Home() {
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [searchIp, setSearchIp] = useState('');

  // Fonction pour envoyer l'action à notre API proxy, qui l'enverra à Splunk
  const logAction = async (actionType, details = {}) => {
    const logEvent = {
      action: actionType,
      user: currentUser.name,
      role: currentUser.role,
      ip: currentUser.ip,
      patient: selectedPatient?.name || 'N/A',
      details: details,
      timestamp: new Date().toISOString()
    };

    try {
      await fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logEvent)
      });
      console.log("Log sent to Splunk:", logEvent);
    } catch (error) {
      console.error("Error sending log:", error);
    }
  };

  const handleLogin = () => {
    logAction('LOGIN_SUCCESS');
  };

  const handleViewDocument = (docName) => {
    logAction('VIEW_PATIENT_DOCUMENT', { document: docName });
    alert(`Ouverture du document : ${docName}`);
  };

  const handleDownloadDocument = (docName) => {
    logAction('DOWNLOAD_PATIENT_DOCUMENT', { document: docName });
  };

  // Simulation d'une recherche suspecte (pour déclencher l'agent IA)
  const handleSuspiciousSearch = () => {
    const logEvent = {
      action: 'SEARCH_PATIENT_RECORD',
      user: currentUser.name,
      role: currentUser.role,
      ip: searchIp || currentUser.ip, // Utilise l'IP saisie si c'est une simulation d'attaque
      details: { query: "Tous les patients VIH", status: "UNAUTHORIZED_ACCESS_ATTEMPT" },
      timestamp: new Date().toISOString()
    };
    
    // Envoi direct du log suspect
    fetch('/api/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(logEvent)
    });
    alert("Tentative d'accès non autorisé simulée ! Allez vérifier Splunk et votre Dashboard SOC.");
  };

  return (
    <div>
      <div className="header">
        <h1>🏥 CHU Médical Platform</h1>
        <button className="btn btn-success" onClick={handleLogin}>Connexion (Dr. House)</button>
      </div>

      <div className="container">
        <div className="card" style={{ borderLeft: '5px solid #d13438' }}>
          <h3>⚡ Simuler une attaque (Pour le hackathon)</h3>
          <p>Simulez une recherche illégale depuis une IP externe pour déclencher l'Agent IA.</p>
          <input 
            placeholder="IP Attaquant (ex: 203.0.113.42)" 
            value={searchIp} 
            onChange={(e) => setSearchIp(e.target.value)} 
          />
          <button className="btn btn-danger" onClick={handleSuspiciousSearch}>
            Lancer la recherche illégale
          </button>
        </div>

        <h2>Dossiers Patients</h2>
        {!selectedPatient ? (
          <div>
            {patients.map(p => (
              <div key={p.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3>{p.name}</h3>
                  <p>Service : {p.service}</p>
                </div>
                <button className="btn btn-primary" onClick={() => setSelectedPatient(p)}>
                  Accéder au dossier
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="card">
            <button className="btn" onClick={() => setSelectedPatient(null)} style={{ marginBottom: '1rem' }}>
              ← Retour à la liste
            </button>
            <h2>Dossier de {selectedPatient.name}</h2>
            <p>Service : {selectedPatient.service}</p>
            <h3>Documents Médicaux :</h3>
            <ul>
              {selectedPatient.docs.map(doc => (
                <li key={doc} style={{ margin: '10px 0' }}>
                  {doc} 
                  <button className="btn btn-primary" style={{ marginLeft: '10px' }} onClick={() => handleViewDocument(doc)}>Voir</button>
                  <button className="btn" onClick={() => handleDownloadDocument(doc)}>Télécharger</button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}