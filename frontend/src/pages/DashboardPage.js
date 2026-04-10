import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import CookiesInstructionsBox from '../components/CookiesInstructionsBox';
import ReturningLeagueSelector from '../components/ReturningLeagueSelector';
import { safeFetch, fetchWithRetry } from '../utils/api';
import { getCookie } from '../utils/csrf';
import '../components/styles/league.css';

const DashboardPage = () => {
  const [leagues, setLeagues] = useState([]);
  const [fetchError, setFetchError] = useState(null);
  const [removingId, setRemovingId] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    league_id: '',
    league_year: 2025,
    swid: '',
    espn_s2: '',
  });
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const navigate = useNavigate();

  if (fetchError) throw fetchError;

  const loadLeagues = () => {
    safeFetch('/api/leagues/', {}, false, 2)
      .then((data) => {
        const all = [
          ...(data.leagues_current_year || []),
          ...(data.leagues_previous_year || []),
        ];
        setLeagues(all);
      })
      .catch((error) => {
        console.error('Error fetching leagues:', error);
        setFetchError(error);
      });
  };

  useEffect(() => {
    fetch('/api/get-csrf-token/', { credentials: 'include' }).catch(() => {});
    loadLeagues();
  }, []);

  const handleRemove = async (leagueDbId) => {
    if (!window.confirm('Remove this league from your account?')) return;
    setRemovingId(leagueDbId);
    try {
      const csrftoken = getCookie('csrftoken');
      const response = await fetchWithRetry(
        `/api/league/${leagueDbId}/delete/`,
        {
          method: 'POST',
          headers: { 'X-CSRFToken': csrftoken },
          credentials: 'include',
        },
        1
      );
      if (response.ok) {
        setLeagues((prev) => prev.filter((l) => l.id !== leagueDbId));
      }
    } catch (err) {
      console.error('Failed to remove league:', err);
    } finally {
      setRemovingId(null);
    }
  };

  const handleFormChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);
    try {
      const csrftoken = getCookie('csrftoken');
      const response = await fetchWithRetry(
        '/api/league-input/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
          },
          credentials: 'include',
          body: JSON.stringify(formData),
        },
        2
      );
      const data = await response.json();
      if (response.status === 409 && data.code === 'too_soon_league') {
        navigate(
          `/fantasy_stats/uh-oh-too-early/league-homepage/${formData.league_year}/${formData.league_id}`
        );
      } else if (response.ok && data.redirect_url) {
        navigate(data.redirect_url);
      } else {
        setFormError(data.error || 'Failed to add league.');
      }
    } catch {
      setFormError('An unexpected error occurred.');
    } finally {
      setFormLoading(false);
    }
  };

  // Group leagues by year, sorted descending
  const byYear = leagues.reduce((acc, league) => {
    const y = league.league_year;
    if (!acc[y]) acc[y] = [];
    acc[y].push(league);
    return acc;
  }, {});
  const sortedYears = Object.keys(byYear).sort((a, b) => b - a);

  return (
    <div>
      <div className="league-content">
        <Header />
        <h2>My Leagues</h2>

        {leagues.length === 0 ? (
          <p>You have no leagues yet. Add one below!</p>
        ) : (
          sortedYears.map((year) => (
            <div key={year} style={{ marginBottom: '1.5rem' }}>
              <h3>{year} Season</h3>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {byYear[year].map((league) => (
                  <li
                    key={league.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <Link
                      to={`/fantasy_stats/league/${league.league_year}/${league.league_id}/`}
                    >
                      {league.league_name} ({league.league_id})
                    </Link>
                    <button
                      onClick={() => handleRemove(league.id)}
                      disabled={removingId === league.id}
                      style={{
                        fontSize: '0.75rem',
                        color: '#dc3545',
                        background: 'none',
                        border: '1px solid #dc3545',
                        borderRadius: 4,
                        cursor: 'pointer',
                        padding: '2px 8px',
                      }}
                    >
                      {removingId === league.id ? 'Removing…' : 'Remove'}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}

        <ReturningLeagueSelector dropdownClassName="league-dropdown" />

        <div style={{ marginTop: '1.5rem' }}>
          <button onClick={() => setShowAddForm((v) => !v)}>
            {showAddForm ? 'Cancel' : '+ Add League'}
          </button>

          {showAddForm && (
            <div style={{ marginTop: '1rem' }}>
              <h3>Add a league manually</h3>
              <form onSubmit={handleAddSubmit}>
                <label>League ID: </label>
                <br />
                <input
                  type="text"
                  name="league_id"
                  value={formData.league_id}
                  onChange={handleFormChange}
                />
                <br />
                <label>League year: </label>
                <br />
                <input
                  type="number"
                  min="2017"
                  name="league_year"
                  value={formData.league_year}
                  onChange={handleFormChange}
                />
                <br />
                <label>SWID: </label>
                <br />
                <input
                  type="password"
                  name="swid"
                  value={formData.swid}
                  onChange={handleFormChange}
                />
                <br />
                <label>ESPN s2: </label>
                <br />
                <input
                  type="password"
                  name="espn_s2"
                  value={formData.espn_s2}
                  onChange={handleFormChange}
                />
                {formError && <p className="error-message">{formError}</p>}
                <div className="button-container">
                  <button type="submit" disabled={formLoading}>
                    {formLoading ? 'Adding…' : 'Add League'}
                  </button>
                </div>
              </form>
              <CookiesInstructionsBox />
            </div>
          )}
        </div>

        {/* Playoff Pool Link */}
        <div
          style={{
            marginTop: '2rem',
            padding: '1rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
          }}
        >
          <h3 style={{ marginBottom: '0.5rem' }}>NFL Playoff Pool</h3>
          <p style={{ marginBottom: '1rem', fontSize: '14px', color: '#6c757d' }}>
            Draft players from playoff teams and compete with your friends!
          </p>
          <Link
            to="/playoff-pool"
            style={{
              display: 'inline-block',
              backgroundColor: '#28a745',
              color: 'white',
              padding: '10px 20px',
              textDecoration: 'none',
              borderRadius: '5px',
              fontWeight: 'bold',
            }}
          >
            Enter Playoff Pool →
          </Link>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default DashboardPage;
