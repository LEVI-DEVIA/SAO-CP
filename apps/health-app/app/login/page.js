'use client';

import { useState } from 'react';
import doctors from '../../lib/doctors.json';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const [matricule, setMatricule] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const router = useRouter();

    const logAction = async (action, details) => {
        await fetch('/api/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, ip: window?.localStorage.getItem('simulated_ip') || '127.0.0.1', details })
        });
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        const doctor = doctors.find(d => d.matricule === matricule && d.password === password);

        if (doctor) {
            await logAction('LOGIN_SUCCESS', { matricule, doctorName: doctor.name });
            localStorage.setItem('currentUser', JSON.stringify(doctor));
            router.push('/dashboard');
        } else {
            await logAction('LOGIN_FAILED', { matricule, reason: "Invalid credentials" });
            setError('Matricule ou mot de passe incorrect');
        }
    };

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#f0f4f8' }}>
            <div style={{ backgroundColor: 'white', padding: '2rem', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', width: '100%', maxWidth: '400px' }}>
                <h2 style={{ textAlign: 'center', color: '#005a9e' }}>🏥 Connexion CHU</h2>
                <form onSubmit={handleLogin}>
                    <div style={{ marginBottom: '1rem' }}>
                        <label>Matricule</label>
                        <input
                            type="text"
                            value={matricule}
                            onChange={(e) => setMatricule(e.target.value)}
                            placeholder="Ex: DOC001"
                            style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem', boxSizing: 'border-box' }}
                            required
                        />
                    </div>
                    <div style={{ marginBottom: '1rem' }}>
                        <label>Mot de passe générique</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Mot de passe"
                            style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem', boxSizing: 'border-box' }}
                            required
                        />
                    </div>
                    {error && <p style={{ color: 'red', textAlign: 'center', fontSize: '0.9rem' }}>{error}</p>}
                    <button type="submit" style={{ width: '100%', padding: '0.75rem', backgroundColor: '#005a9e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                        Se connecter
                    </button>
                </form>
            </div>
        </div>
    );
}