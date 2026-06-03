'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { initialPatients } from '../../lib/mockData';

export default function DashboardPage() {
    const [user, setUser] = useState(null);
    const [patients, setPatients] = useState(initialPatients);
    const [selectedPatient, setSelectedPatient] = useState(null);
    const [newDocName, setNewDocName] = useState('');
    const [attackIp, setAttackIp] = useState('');
    const router = useRouter();

    useEffect(() => {
        const storedUser = localStorage.getItem('currentUser');
        if (!storedUser) {
            router.push('/login');
        } else {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    const logAction = async (action, details = {}) => {
        const ip = attackIp || '127.0.0.1'; // Prend l'IP de l'attaquant si remplie, sinon IP normale
        await fetch('/api/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, user: user?.name || 'Unknown', role: user?.specialty || 'Unknown', ip, details })
        });
    };

    const handleLogout = async () => {
        await logAction('LOGOUT');
        localStorage.removeItem('currentUser');
        router.push('/login');
    };

    const handleUploadDoc = async () => {
        if (!newDocName || !selectedPatient) return;

        // Mise à jour locale (simulée)
        const updatedPatients = patients.map(p => {
            if (p.id === selectedPatient.id) {
                return { ...p, docs: [...p.docs, newDocName] };
            }
            return p;
        });
        setPatients(updatedPatients);
        setSelectedPatient({ ...selectedPatient, docs: [...selectedPatient.docs, newDocName] });

        // Log vers Splunk
        await logAction('UPLOAD_DOCUMENT', { patient: selectedPatient.name, document: newDocName });
        setNewDocName('');
    };

    const handleDeleteDoc = async (docName) => {
        const updatedPatients = patients.map(p => {
            if (p.id === selectedPatient.id) {
                return { ...p, docs: p.docs.filter(d => d !== docName) };
            }
            return p;
        });
        setPatients(updatedPatients);
        setSelectedPatient({ ...selectedPatient, docs: selectedPatient.docs.filter(d => d !== docName) });

        // Log vers Splunk
        await logAction('DELETE_DOCUMENT', { patient: selectedPatient.name, document: docName });
    };

    const handleSuspiciousSearch = async () => {
        await logAction('UNAUTHORIZED_ACCESS_ATTEMPT', { query: "Recherche globale dossiers VIH", status: "BLOCKED_BY_SYSTEM" });
        alert("Tentative d'accès non autorisé simulée ! Allez vérifier Splunk et votre Dashboard SOC.");
    };

    if (!user) return <p>Chargement...</p>;

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#f0f4f8' }}>
            {/* Header */}
            <div style={{ background: '#005a9e', color: 'white', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1>🏥 CHU Médical Platform</h1>
                <div>
                    <span>Bonjour, {user.name} ({user.matricule})</span>
                    <button onClick={handleLogout} style={{ marginLeft: '1rem', padding: '0.5rem 1rem', background: '#d13438', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Déconnexion</button>
                </div>
            </div>

            <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem' }}>
                {/* Zone Attaque */}
                <div style={{ background: 'white', borderLeft: '5px solid #d13438', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                    <h3>⚡ Simuler une attaque (Pour le hackathon)</h3>
                    <p>Simulez une recherche illégale depuis une IP externe pour déclencher l'Agent IA.</p>
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <input placeholder="IP Attaquant (ex: 203.0.113.42)" value={attackIp} onChange={(e) => setAttackIp(e.target.value)} style={{ padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }} />
                        <button onClick={handleSuspiciousSearch} style={{ padding: '0.5rem 1rem', background: '#d13438', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Lancer la recherche illégale</button>
                    </div>
                </div>

                {/* Liste des patients ou Dossier patient */}
                {!selectedPatient ? (
                    <div>
                        <h2>Dossiers Patients</h2>
                        {patients.map(p => (
                            <div key={p.id} style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', marginBottom: '1rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <h3>{p.name}</h3>
                                    <p>Service : {p.service} | Documents : {p.docs.length}</p>
                                </div>
                                <button onClick={() => setSelectedPatient(p)} style={{ padding: '0.5rem 1rem', background: '#005a9e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Accéder au dossier</button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                        <button onClick={() => setSelectedPatient(null)} style={{ marginBottom: '1rem', padding: '0.5rem 1rem', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer' }}>← Retour à la liste</button>
                        <h2>Dossier de {selectedPatient.name} ({selectedPatient.service})</h2>

                        <div style={{ marginTop: '1rem', padding: '1rem', background: '#e8f0fe', borderRadius: '4px' }}>
                            <h4>Ajouter un document (Upload simulé)</h4>
                            <div style={{ display: 'flex', gap: '10px' }}>
                                <input
                                    type="text"
                                    placeholder="Nom du fichier (ex: Resultats_Biologie.pdf)"
                                    value={newDocName}
                                    onChange={(e) => setNewDocName(e.target.value)}
                                    style={{ flexGrow: 1, padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                                />
                                <button onClick={handleUploadDoc} style={{ padding: '0.5rem 1rem', background: '#107c10', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Uploader</button>
                            </div>
                        </div>

                        <h3 style={{ marginTop: '1.5rem' }}>Documents Médicaux :</h3>
                        {selectedPatient.docs.length === 0 ? <p>Aucun document.</p> : (
                            <ul style={{ listStyleType: 'none', padding: 0 }}>
                                {selectedPatient.docs.map(doc => (
                                    <li key={doc} style={{ margin: '10px 0', padding: '10px', background: '#f8f9fa', border: '1px solid #eee', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        📄 {doc}
                                        <div>
                                            <button style={{ marginLeft: '10px', padding: '0.5rem', background: '#005a9e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }} onClick={() => alert(`Visualisation de ${doc}`)}>Voir</button>
                                            <button style={{ marginLeft: '10px', padding: '0.5rem', background: '#d13438', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }} onClick={() => handleDeleteDoc(doc)}>Supprimer</button>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}