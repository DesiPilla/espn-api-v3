"""
NFL utility functions for playoff pool application.
"""
import nflreadpy as nfl
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


def get_current_nfl_season():
    """
    Get the current NFL season year.
    
    Returns:
        int: The current NFL season year
    
    Example:
        >>> season = get_current_nfl_season()
        >>> print(season)
        2025
    """
    return nfl.get_current_season()


@api_view(['GET'])
@permission_classes([AllowAny])
def current_nfl_season_api(request):
    """
    API endpoint to get the current NFL season year.
    
    Returns:
        JsonResponse: JSON response containing the current season year
        
    Example response:
        {
            "current_season": 2025,
            "status": "success"
        }
    """
    try:
        current_season = get_current_nfl_season()
        return JsonResponse({
            'current_season': current_season,
            'status': 'success'
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)