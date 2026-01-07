import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayoffPoolAuth } from '../../components/PlayoffPool/AuthContext';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const LeagueSetup = () => {
  const [formData, setFormData] = useState({
    name: '',
    num_teams: 12,
    positions_included: ['QB', 'RB', 'WR', 'TE', 'K', 'DST'],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [positionOptions, setPositionOptions] = useState([]);
  
  const { user } = usePlayoffPoolAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadScoringSettings();
  }, []);

  const loadScoringSettings = async () => {
    try {
      const data = await playoffPoolAPI.getScoringSettings();
      setPositionOptions(data.position_choices || []);
    } catch (err) {
      console.error('Error loading scoring settings:', err);
      // Fallback to default positions
      setPositionOptions([
        { value: 'QB', label: 'Quarterback' },
        { value: 'RB', label: 'Running Back' },
        { value: 'WR', label: 'Wide Receiver' },
        { value: 'TE', label: 'Tight End' },
        { value: 'K', label: 'Kicker' },
        { value: 'DST', label: 'Defense/Special Teams' },
      ]);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'num_teams' ? parseInt(value) : value,
    });
    if (error) setError(null);
  };

  const handlePositionChange = (position) => {
    const updatedPositions = formData.positions_included.includes(position)
      ? formData.positions_included.filter(p => p !== position)
      : [...formData.positions_included, position];
    
    setFormData({
      ...formData,
      positions_included: updatedPositions,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('League name is required');
      return;
    }
    
    if (formData.positions_included.length === 0) {
      setError('At least one position must be selected');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const league = await playoffPoolAPI.createLeague(formData);
      navigate(`/playoff-pool/league/${league.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create league');
      console.error('Error creating league:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/playoff-pool');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white shadow-md rounded-lg p-6">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">Create New League</h1>
              <p className="text-gray-600 mt-2">
                Set up your playoff pool league configuration
              </p>
            </div>

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              {/* League Name */}
              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="name">
                  League Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                  placeholder="Enter league name"
                />
              </div>

              {/* Number of Teams */}
              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="num_teams">
                  Number of Teams
                </label>
                <select
                  id="num_teams"
                  name="num_teams"
                  value={formData.num_teams}
                  onChange={handleChange}
                  className="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                >
                  {Array.from({ length: 15 }, (_, i) => i + 2).map(num => (
                    <option key={num} value={num}>{num} teams</option>
                  ))}
                </select>
                <p className="text-gray-600 text-sm mt-1">
                  Number of users/teams that can participate in this league
                </p>
              </div>

              {/* Positions */}
              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-bold mb-3">
                  Positions to Include *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {positionOptions.map(position => (
                    <div key={position.value} className="flex items-center">
                      <input
                        type="checkbox"
                        id={`position_${position.value}`}
                        checked={formData.positions_included.includes(position.value)}
                        onChange={() => handlePositionChange(position.value)}
                        className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor={`position_${position.value}`}
                        className="text-gray-700 text-sm"
                      >
                        {position.label} ({position.value})
                      </label>
                    </div>
                  ))}
                </div>
                <p className="text-gray-600 text-sm mt-2">
                  Select which positions players can draft from playoff teams
                </p>
              </div>

              {/* League Summary */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">League Summary</h3>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li><strong>Name:</strong> {formData.name || 'Not set'}</li>
                  <li><strong>Teams:</strong> {formData.num_teams}</li>
                  <li><strong>Positions:</strong> {formData.positions_included.join(', ') || 'None selected'}</li>
                  <li><strong>Admin:</strong> {user?.display_name || user?.username}</li>
                </ul>
              </div>

              {/* Buttons */}
              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className={`font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ${
                    loading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-500 hover:bg-blue-700 text-white'
                  }`}
                >
                  {loading ? 'Creating League...' : 'Create League'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeagueSetup;