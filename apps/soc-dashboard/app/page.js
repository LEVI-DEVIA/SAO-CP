'use client';

import { useState, useEffect, useRef } from 'react';

export default function SOCDashboard() {
    const [alerts, setAlerts] = useState([]);
    const ws = useRef(null);

    useEffect(() => {
        // Connexion au WebSocket de FastAPI
        ws.current = new WebSocket('ws://127.0.0.1:8000/ws');

        ws.current.onmessage = (event) => {
            const newAlert = JSON.parse(event.data);

            setAlerts(prevAlerts => {
                // Si l'alerte existe déjà (mise à jour de statut), on la remplace
                const index = prevAlerts.findIndex(a => a.id === newAlert.id);
                if (index !== -1) {
                    const updated = [...prevAlerts];
                    updated[index] = newAlert;
                    return updated;
                }
                // Sinon, on l'ajoute en haut de la liste
                return [newAlert, ...prevAlerts];
            });
        };

        ws.current.onopen = () => console.log('🛡️ Connecté au Backend FastAPI');
        ws.current.onclose = () => console.log('Déconnecté du Backend');

        return () => ws.current.close();
    }, []);

    const handleDecision = async (alertId, decision) => {
        // Appel API pour mettre à jour le statut dans FastAPI
        await fetch(`http://127.0.0.1:8000/api/alerts/${alertId}?status=${decision}`, {
            method: 'PATCH'
        });
    };

    return (
        <div style={{ backgroundColor: '#0d1117', color: '#c9d1d9', minHeight: '100vh', fontFamily: 'sans-serif' }}>
            <header style={{ padding: '1rem 2rem', backgroundColor: '#161b22', borderBottom: '1px solid #30363d', display: 'flex', justifyContent: 'space-between' }}>
                <h1 style={{ color: '#58a6ff' }}>🛡️ SAO-CP SOC Dashboard</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ height: '10px', width: '10px', backgroundColor: '#3fb950', borderRadius: '50%', display: 'inline-block' }}></span>
                    <span>Live Monitoring</span>
                </div>
            </header>

            <main style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
                <h2>Alertes de l'Agent IA ({alerts.length})</h2>

                {alerts.length === 0 && (
                    <div style={{ textAlign: 'center', marginTop: '4rem', color: '#8b949e' }}>
                        <h3>Aucune alerte pour le moment...</h3>
                        <p>Simulez une attaque sur la plateforme médicale pour voir l'Agent en action.</p>
                    </div>
                )}

                {alerts.map(alert => (
                    <div key={alert.id} style={{
                        backgroundColor: '#161b22',
                        border: `1px solid ${alert.status === 'PENDING_HUMAN_APPROVAL' ? '#d29922' : '#30363d'}`,
                        borderRadius: '8px',
                        padding: '1.5rem',
                        marginBottom: '1rem',
                        boxShadow: alert.status === 'PENDING_HUMAN_APPROVAL' ? '0 0 15px rgba(210, 153, 34, 0.2)' : 'none'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h3 style={{ margin: 0, color: '#ff7b72' }}>🚨 {alert.threat_type}</h3>
                            <span style={{
                                padding: '0.25rem 0.75rem',
                                borderRadius: '12px',
                                fontSize: '0.85rem',
                                fontWeight: 'bold',
                                backgroundColor:
                                    alert.status === 'PENDING_HUMAN_APPROVAL' ? '#d2992233' :
                                        alert.status === 'APPROVED' ? '#3fb95033' : '#f8514933',
                                color:
                                    alert.status === 'PENDING_HUMAN_APPROVAL' ? '#d29922' :
                                        alert.status === 'APPROVED' ? '#3fb950' : '#f85149'
                            }}>
                                {alert.status === 'PENDING_HUMAN_APPROVAL' ? '⏳ EN ATTENTE' :
                                    alert.status === 'APPROVED' ? '✅ APPROUVÉ' : '❌ REJETÉ'}
                            </span>
                        </div>

                        <div style={{ marginBottom: '1rem' }}>
                            <p style={{ color: '#8b949e', margin: '0.5rem 0 0' }}><strong>🤖 Analyse de l'IA :</strong> {alert.ai_reasoning}</p>
                            <p style={{ color: '#79c0ff', margin: '0.5rem 0 0' }}><strong>⚡ Action Proposée :</strong> {alert.proposed_action}</p>
                            <p style={{ color: '#79c0ff', margin: '0.5rem 0 0' }}><strong>📝 Détails :</strong> {alert.action_details}</p>
                        </div>

                        {alert.status === 'PENDING_HUMAN_APPROVAL' && (
                            <div style={{ display: 'flex', gap: '10px', marginTop: '1rem' }}>
                                <button
                                    onClick={() => handleDecision(alert.id, 'APPROVED')}
                                    style={{ flex: 1, padding: '0.75rem', backgroundColor: '#238636', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem' }}
                                >
                                    ✅ Approuver et Exécuter
                                </button>
                                <button
                                    onClick={() => handleDecision(alert.id, 'REJECTED')}
                                    style={{ flex: 1, padding: '0.75rem', backgroundColor: '#da3633', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem' }}
                                >
                                    ❌ Rejeter l'action
                                </button>
                            </div>
                        )}
                    </div>
                ))}
            </main>
        </div>
    );
}