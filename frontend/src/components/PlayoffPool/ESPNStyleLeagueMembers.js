import React, { useState } from 'react';

const ESPNStyleLeagueMembers = ({ 
    league, 
    members, 
    user, 
    isAdmin, 
    handleInviteFriend, 
    confirmRemoveTeam,
    handleClaimTeam,
    handleUnclaimTeam,
    handleCreateTeam,
    leagueId 
}) => {
    const [creatingTeamIndex, setCreatingTeamIndex] = useState(null);
    const [newTeamName, setNewTeamName] = useState('');

    const startCreatingTeam = (index) => {
        setCreatingTeamIndex(index);
        setNewTeamName('');
    };

    const cancelCreatingTeam = () => {
        setCreatingTeamIndex(null);
        setNewTeamName('');
    };

    const saveNewTeam = async () => {
        if (!newTeamName.trim()) return;
        try {
            await handleCreateTeam(newTeamName.trim());
            setCreatingTeamIndex(null);
            setNewTeamName('');
        } catch (err) {
            console.error('Failed to create team:', err);
        }
    };

    const containerStyle = {
        backgroundColor: 'white',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        overflow: 'hidden'
    };

    const headerStyle = {
        backgroundColor: '#f8fafc',
        borderBottom: '1px solid #e2e8f0',
        padding: '16px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
    };

    return (
        <div style={containerStyle}>
            <div style={headerStyle}>
                <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    League Members
                </h2>
                <span style={{ fontSize: '14px', fontWeight: '500', color: '#6b7280' }}>
                    {league?.name}
                </span>
            </div>

            {/* Table using CSS Grid for proper column layout */}
            <div style={{ display: 'grid', gridTemplateColumns: '8% 8% 25% 25% 22% 12%', backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0' }}>
                <div style={{ padding: '12px 8px', fontSize: '12px', fontWeight: '500', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'center' }}>#</div>
                <div style={{ padding: '12px 8px', fontSize: '12px', fontWeight: '500', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'center' }}>TEAM</div>
                <div style={{ padding: '12px 8px', fontSize: '12px', fontWeight: '500', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>TEAM NAME</div>
                <div style={{ padding: '12px 8px', fontSize: '12px', fontWeight: '500', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>MANAGER</div>
                <div style={{ padding: '12px 8px', fontSize: '12px', fontWeight: '500', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'center' }}>STATUS</div>
                <div style={{ padding: '12px 8px', fontSize: '12px', fontWeight: '500', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'center' }}>ACTION</div>
            </div>

            {/* Table Body using CSS Grid */}
            <div style={{ borderTop: '1px solid #f1f5f9' }}>

                {(() => {
                    const allSlots = [];
                    
                    // Add actual teams
                    members.forEach((member, index) => {
                        allSlots.push({
                            type: 'team',
                            data: member,
                            index: index + 1
                        });
                    });
                    
                    // Add empty slots
                    const emptySlots = (league?.num_teams || 0) - members.length;
                    for (let i = 0; i < emptySlots; i++) {
                        allSlots.push({
                            type: 'empty',
                            index: members.length + i + 1
                        });
                    }
                    
                    return allSlots.map((slot) => (
                        <div key={slot.type === 'team' ? slot.data.id : `empty-${slot.index}`} 
                             style={{ 
                                display: 'grid', 
                                gridTemplateColumns: '8% 8% 25% 25% 22% 12%',
                                padding: '12px 0',
                                borderBottom: '1px solid #f1f5f9',
                                alignItems: 'center',
                                transition: 'background-color 0.15s'
                             }}
                             onMouseEnter={e => e.target.style.backgroundColor = '#f8fafc'}
                             onMouseLeave={e => e.target.style.backgroundColor = 'transparent'}>
                            
                            {/* Position Number */}
                            <div style={{ textAlign: 'center', padding: '0 8px' }}>
                                <span style={{ fontSize: '14px', fontWeight: '500', color: '#1f2937' }}>
                                    {slot.index}
                                </span>
                            </div>
                            
                            {/* Team Logo/Icon */}
                            <div style={{ textAlign: 'center', padding: '0 8px' }}>
                                {slot.type === 'team' ? (
                                    <div style={{
                                        width: '32px',
                                        height: '32px',
                                        background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                                        margin: '0 auto'
                                    }}>
                                        <span style={{ color: 'white', fontSize: '12px', fontWeight: 'bold' }}>
                                            {slot.data.team_name.charAt(0).toUpperCase()}
                                        </span>
                                    </div>
                                ) : (
                                    <div style={{
                                        width: '32px',
                                        height: '32px',
                                        backgroundColor: '#e2e8f0',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        margin: '0 auto'
                                    }}>
                                        <span style={{ color: '#94a3b8', fontSize: '12px' }}>+</span>
                                    </div>
                                )}
                            </div>
                            
                            {/* Team Name */}
                            <div style={{ padding: '0 8px' }}>
                                {slot.type === 'team' ? (
                                    <div style={{ 
                                        fontSize: '14px', 
                                        fontWeight: '500', 
                                        color: '#1f2937',
                                        cursor: 'pointer'
                                    }}>
                                        {slot.data.team_name}
                                    </div>
                                ) : (
                                    creatingTeamIndex === slot.index ? (
                                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                                            <input
                                                type="text"
                                                value={newTeamName}
                                                onChange={(e) => setNewTeamName(e.target.value)}
                                                placeholder="Enter team name..."
                                                style={{
                                                    fontSize: '14px',
                                                    padding: '4px 8px',
                                                    border: '1px solid #d1d5db',
                                                    borderRadius: '4px',
                                                    flex: 1,
                                                    outline: 'none'
                                                }}
                                                autoFocus
                                                onKeyPress={(e) => {
                                                    if (e.key === 'Enter') saveNewTeam();
                                                    if (e.key === 'Escape') cancelCreatingTeam();
                                                }}
                                            />
                                        </div>
                                    ) : (
                                        <div style={{ fontSize: '14px', color: '#9ca3af', fontStyle: 'italic' }}>
                                            Available
                                        </div>
                                    )
                                )}
                            </div>
                            
                            {/* Manager Name */}
                            <div style={{ padding: '0 8px' }}>
                                {slot.type === 'team' ? (
                                    <div style={{ fontSize: '14px', color: '#1f2937' }}>
                                        {slot.data.user ? slot.data.user.username : 'Unclaimed'}
                                    </div>
                                ) : (
                                    <div style={{ fontSize: '14px', color: '#9ca3af' }}>-</div>
                                )}
                            </div>
                            
                            {/* Status */}
                            <div style={{ textAlign: 'center', padding: '0 8px' }}>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', justifyContent: 'center', alignItems: 'center' }}>
                                    {slot.type === 'team' ? (
                                        <>
                                            {slot.data.user ? (
                                                <span style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    padding: '4px 8px',
                                                    borderRadius: '9999px',
                                                    fontSize: '12px',
                                                    fontWeight: '500',
                                                    backgroundColor: '#dcfce7',
                                                    color: '#166534'
                                                }}>
                                                    Joined
                                                </span>
                                            ) : (
                                                <span style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    padding: '4px 8px',
                                                    borderRadius: '9999px',
                                                    fontSize: '12px',
                                                    fontWeight: '500',
                                                    backgroundColor: '#fef3c7',
                                                    color: '#92400e'
                                                }}>
                                                    Unclaimed
                                                </span>
                                            )}
                                            {slot.data.is_admin && (
                                                <span style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    padding: '4px 8px',
                                                    borderRadius: '9999px',
                                                    fontSize: '12px',
                                                    fontWeight: '500',
                                                    backgroundColor: '#dbeafe',
                                                    color: '#1e40af'
                                                }}>
                                                    Admin
                                                </span>
                                            )}
                                            {slot.data.user && slot.data.user.id === user?.id && (
                                                <span style={{
                                                    display: 'inline-flex',
                                                    alignItems: 'center',
                                                    padding: '4px 8px',
                                                    borderRadius: '9999px',
                                                    fontSize: '12px',
                                                    fontWeight: '500',
                                                    backgroundColor: '#e9d5ff',
                                                    color: '#7c3aed'
                                                }}>
                                                    You
                                                </span>
                                            )}
                                        </>
                                    ) : (
                                        <span style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            padding: '4px 8px',
                                            borderRadius: '9999px',
                                            fontSize: '12px',
                                            fontWeight: '500',
                                            backgroundColor: '#f1f5f9',
                                            color: '#475569'
                                        }}>
                                            Open
                                        </span>
                                    )}
                                </div>
                            </div>
                            
                            {/* Action */}
                            <div style={{ textAlign: 'center', padding: '0 8px' }}>
                                <div style={{ display: 'flex', gap: '4px', justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap' }}>
                                    {slot.type === 'team' ? (
                                        <>
                                            {!slot.data.user ? (
                                                // Unclaimed team actions
                                                <>
                                                    <button
                                                        onClick={() => handleClaimTeam(slot.data)}
                                                        style={{
                                                            display: 'inline-flex',
                                                            alignItems: 'center',
                                                            padding: '4px 8px',
                                                            border: '1px solid #34d399',
                                                            borderRadius: '4px',
                                                            fontSize: '12px',
                                                            fontWeight: '500',
                                                            color: '#059669',
                                                            backgroundColor: '#ecfdf5',
                                                            cursor: 'pointer',
                                                            transition: 'background-color 0.15s'
                                                        }}
                                                        title="Claim Team"
                                                    >
                                                        Claim
                                                    </button>
                                                    {isAdmin && (
                                                        <>
                                                            <button
                                                                onClick={() => handleInviteFriend(slot.data.id, slot.data.team_name)}
                                                                style={{
                                                                    display: 'inline-flex',
                                                                    alignItems: 'center',
                                                                    padding: '4px 8px',
                                                                    border: '1px solid #93c5fd',
                                                                    borderRadius: '4px',
                                                                    fontSize: '12px',
                                                                    fontWeight: '500',
                                                                    color: '#1d4ed8',
                                                                    backgroundColor: '#eff6ff',
                                                                    cursor: 'pointer',
                                                                    transition: 'background-color 0.15s'
                                                                }}
                                                                title="Send Invite"
                                                            >
                                                                Invite
                                                            </button>
                                                            <button
                                                                onClick={() => confirmRemoveTeam(slot.data)}
                                                                style={{
                                                                    display: 'inline-flex',
                                                                    alignItems: 'center',
                                                                    padding: '4px 8px',
                                                                    border: '1px solid #fca5a5',
                                                                    borderRadius: '4px',
                                                                    fontSize: '12px',
                                                                    fontWeight: '500',
                                                                    color: '#dc2626',
                                                                    backgroundColor: '#fef2f2',
                                                                    cursor: 'pointer',
                                                                    transition: 'background-color 0.15s'
                                                                }}
                                                                title="Delete Team Permanently"
                                                            >
                                                                Remove
                                                            </button>
                                                        </>
                                                    )}
                                                </>
                                            ) : (
                                                // Claimed team actions
                                                <>
                                                    {(slot.data.user.id === user?.id || isAdmin) && (
                                                        <button
                                                            onClick={() => handleUnclaimTeam(slot.data)}
                                                            style={{
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                padding: '4px 8px',
                                                                border: '1px solid #f59e0b',
                                                                borderRadius: '4px',
                                                                fontSize: '12px',
                                                                fontWeight: '500',
                                                                color: '#d97706',
                                                                backgroundColor: '#fef3c7',
                                                                cursor: 'pointer',
                                                                transition: 'background-color 0.15s'
                                                            }}
                                                            title="Make Team Available for Others"
                                                        >
                                                            Unclaim
                                                        </button>
                                                    )}
                                                    {isAdmin && (
                                                        <button
                                                            onClick={() => confirmRemoveTeam(slot.data)}
                                                            style={{
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                padding: '4px 8px',
                                                                border: '1px solid #fca5a5',
                                                                borderRadius: '4px',
                                                                fontSize: '12px',
                                                                fontWeight: '500',
                                                                color: '#dc2626',
                                                                backgroundColor: '#fef2f2',
                                                                cursor: 'pointer',
                                                                transition: 'background-color 0.15s'
                                                            }}
                                                            title="Delete Team Permanently"
                                                        >
                                                            Remove
                                                        </button>
                                                    )}
                                                </>
                                            )}
                                        </>
                                    ) : (
                                        // Empty slot actions
                                        creatingTeamIndex === slot.index ? (
                                            <>
                                                <button
                                                    onClick={saveNewTeam}
                                                    disabled={!newTeamName.trim()}
                                                    style={{
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        padding: '4px 8px',
                                                        border: '1px solid #34d399',
                                                        borderRadius: '4px',
                                                        fontSize: '12px',
                                                        fontWeight: '500',
                                                        color: !newTeamName.trim() ? '#9ca3af' : '#059669',
                                                        backgroundColor: !newTeamName.trim() ? '#f3f4f6' : '#ecfdf5',
                                                        cursor: !newTeamName.trim() ? 'not-allowed' : 'pointer',
                                                        transition: 'background-color 0.15s'
                                                    }}
                                                    title="Save Team"
                                                >
                                                    Save
                                                </button>
                                                <button
                                                    onClick={cancelCreatingTeam}
                                                    style={{
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        padding: '4px 8px',
                                                        border: '1px solid #d1d5db',
                                                        borderRadius: '4px',
                                                        fontSize: '12px',
                                                        fontWeight: '500',
                                                        color: '#6b7280',
                                                        backgroundColor: '#f9fafb',
                                                        cursor: 'pointer',
                                                        transition: 'background-color 0.15s'
                                                    }}
                                                    title="Cancel"
                                                >
                                                    Cancel
                                                </button>
                                            </>
                                        ) : (
                                            isAdmin && (
                                                <button
                                                    onClick={() => startCreatingTeam(slot.index)}
                                                    style={{
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        padding: '4px 8px',
                                                        border: '1px solid #a78bfa',
                                                        borderRadius: '4px',
                                                        fontSize: '12px',
                                                        fontWeight: '500',
                                                        color: '#7c3aed',
                                                        backgroundColor: '#f3f4f6',
                                                        cursor: 'pointer',
                                                        transition: 'background-color 0.15s'
                                                    }}
                                                    title="Create Team"
                                                >
                                                    Create Team
                                                </button>
                                            )
                                        )
                                    )}
                                </div>
                            </div>
                        </div>
                    ));
                })()}
            </div>

            {/* Footer Actions */}
            <div style={{
                backgroundColor: '#f8fafc',
                padding: '16px 24px',
                borderTop: '1px solid #e2e8f0'
            }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ fontSize: '14px', color: '#4b5563' }}>
                        <strong>{members.length}</strong> of <strong>{league?.num_teams}</strong> teams filled
                    </div>
                    {members.length < league?.num_teams && (
                        <button
                            onClick={() => {
                                const inviteLink = `${window.location.origin}/playoff-pool/join?league=${leagueId}`;
                                const message = `Join my NFL playoff pool "${league?.name}"! Click this link to join: ${inviteLink}`;
                                
                                if (navigator.clipboard) {
                                    navigator.clipboard.writeText(message)
                                        .then(() => {
                                            alert("Invite link copied to clipboard!");
                                        })
                                        .catch(() => {
                                            prompt("Copy this invite message:", message);
                                        });
                                } else {
                                    prompt("Copy this invite message:", message);
                                }
                            }}
                            style={{
                                width: '100%',
                                backgroundColor: '#2563eb',
                                color: 'white',
                                fontWeight: '500',
                                padding: '8px 16px',
                                borderRadius: '8px',
                                border: 'none',
                                cursor: 'pointer',
                                transition: 'background-color 0.15s'
                            }}
                            onMouseOver={e => e.target.style.backgroundColor = '#1d4ed8'}
                            onMouseOut={e => e.target.style.backgroundColor = '#2563eb'}
                        >
                            📧 Copy Invite Link
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ESPNStyleLeagueMembers;