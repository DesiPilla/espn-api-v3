import axios from 'axios';
import { getCookie } from '../csrf';

const API_BASE_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:8001' : '';

class PlayoffPoolAPI {
    constructor() {
        this.api = axios.create({
            baseURL: `${API_BASE_URL}/playoff-pool/`,
            headers: {
                "Content-Type": "application/json",
            },
            withCredentials: true, // Include cookies for CSRF
        });

        // Add token and CSRF to requests
        this.api.interceptors.request.use(
            (config) => {
                // Add auth token if available
                const token = localStorage.getItem("playoffPoolToken");
                if (token) {
                    config.headers.Authorization = `Token ${token}`;
                }

                // Add CSRF token for POST/PUT/PATCH/DELETE requests
                if (
                    ["post", "put", "patch", "delete"].includes(config.method)
                ) {
                    const csrfToken = getCookie("csrftoken");
                    if (csrfToken) {
                        config.headers["X-CSRFToken"] = csrfToken;
                    }
                }

                return config;
            },
            (error) => Promise.reject(error)
        );
    }

    // Initialize CSRF token (call this before making any requests)
    async initializeCSRF() {
        try {
            await fetch(`${API_BASE_URL}/api/get-csrf-token/`, {
                credentials: "include",
            });
        } catch (error) {
            console.error("Error fetching CSRF token:", error);
        }
    }

    // Authentication
    async login(username, password) {
        const response = await this.api.post("auth/login/", {
            username,
            password,
        });
        if (response.data.token) {
            localStorage.setItem("playoffPoolToken", response.data.token);
            localStorage.setItem(
                "playoffPoolUser",
                JSON.stringify(response.data.user)
            );
        }
        return response.data;
    }

    async register(userData) {
        const response = await this.api.post("auth/register/", userData);
        if (response.data.token) {
            localStorage.setItem("playoffPoolToken", response.data.token);
            localStorage.setItem(
                "playoffPoolUser",
                JSON.stringify(response.data.user)
            );
        }
        return response.data;
    }

    logout() {
        localStorage.removeItem("playoffPoolToken");
        localStorage.removeItem("playoffPoolUser");
    }

    getCurrentUser() {
        const user = localStorage.getItem("playoffPoolUser");
        return user ? JSON.parse(user) : null;
    }

    isAuthenticated() {
        return !!localStorage.getItem("playoffPoolToken");
    }

    // Leagues
    async getLeagues() {
        const response = await this.api.get("api/leagues/");
        return response.data;
    }

    async getLeague(leagueId) {
        const response = await this.api.get(`api/leagues/${leagueId}/`);
        return response.data;
    }

    async createLeague(leagueData) {
        const response = await this.api.post("api/leagues/", leagueData);
        return response.data;
    }

    async deleteLeague(leagueId) {
        const response = await this.api.delete(`api/leagues/${leagueId}/`);
        return response.data;
    }

    async joinLeague(leagueId, teamName, confirmMultiple = false) {
        const response = await this.api.post(`api/leagues/${leagueId}/join/`, {
            team_name: teamName,
            confirm_multiple: confirmMultiple,
        });
        return response.data;
    }

    async createTeam(leagueId, teamName) {
        const response = await this.api.post(
            `api/leagues/${leagueId}/create_team/`,
            { team_name: teamName }
        );
        return response.data;
    }

    async claimTeam(leagueId, teamId, confirmMultiple = false) {
        const response = await this.api.post(
            `api/leagues/${leagueId}/claim_team/`,
            {
                team_id: teamId,
                confirm_multiple: confirmMultiple,
            }
        );
        return response.data;
    }

    async removeTeam(leagueId, teamId) {
        console.log("API: Removing team", teamId, "from league", leagueId);
        const url = `api/leagues/${leagueId}/teams/${teamId}/`;
        console.log("API: DELETE request to:", url);
        const response = await this.api.delete(url);
        console.log("API: Remove team response:", response);
        return response.data;
    }

    async unclaimTeam(leagueId, teamId) {
        const response = await this.api.post(
            `api/leagues/${leagueId}/unclaim_team/`,
            { team_id: teamId }
        );
        return response.data;
    }

    async getLeagueInfo(leagueId) {
        const response = await this.api.get(`league-info/${leagueId}/`);
        return response.data;
    }

    async getLeagueMembers(leagueId) {
        const response = await this.api.get(`api/leagues/${leagueId}/members/`);
        return response.data;
    }

    // Draft
    async getAvailablePlayers(leagueId) {
        const response = await this.api.get(
            `api/leagues/${leagueId}/available_players/`
        );
        return response.data;
    }

    async draftPlayer(leagueId, gsisId, userId, teamId = null) {
        const payload = {
            gsis_id: gsisId,
        };

        // Prefer team_id over user_id for specificity
        if (teamId) {
            payload.team_id = teamId;
        } else {
            payload.user_id = userId;
        }

        const response = await this.api.post(
            `api/leagues/${leagueId}/draft_player/`,
            payload
        );
        return response.data;
    }

    async completeDraft(leagueId) {
        const response = await this.api.post(
            `api/leagues/${leagueId}/complete_draft/`
        );
        return response.data;
    }

    async undoDraft(leagueId) {
        const response = await this.api.post(
            `api/leagues/${leagueId}/undo_draft/`
        );
        return response.data;
    }

    // Teams
    async getDraftedTeams(leagueId) {
        const response = await this.api.get(
            `api/leagues/${leagueId}/drafted_teams/`
        );
        return response.data;
    }

    // Settings
    async getScoringSettings() {
        const response = await this.api.get("scoring-settings/");
        return response.data;
    }
}

export default new PlayoffPoolAPI();