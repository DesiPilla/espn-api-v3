from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
import pytz
from .models import League, LeagueMembership, DraftedTeam, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'display_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    display_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'display_name']
    
    def create(self, validated_data):
        display_name = validated_data.pop('display_name', '')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user, display_name=display_name)
        return user


class LeagueSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    user_membership = serializers.SerializerMethodField()
    created_at_est = serializers.SerializerMethodField()
    draft_started_at_est = serializers.SerializerMethodField()
    draft_completed_at_est = serializers.SerializerMethodField()

    class Meta:
        model = League
        fields = [
            "id",
            "name",
            "created_by",
            "created_at",
            "created_at_est",
            "num_teams",
            "positions_included",
            "scoring_settings",
            "is_draft_complete",
            "draft_started_at",
            "draft_started_at_est",
            "draft_completed_at",
            "draft_completed_at_est",
            "member_count",
            "user_membership",
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'draft_started_at', 'draft_completed_at']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_user_membership(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                # Get all memberships for this user in this league
                memberships = LeagueMembership.objects.filter(
                    user=request.user, league=obj
                )
                if memberships.exists():
                    # Prefer admin membership if available, otherwise get the first one
                    membership = (
                        memberships.filter(is_admin=True).first() or memberships.first()
                    )
                    return LeagueMembershipSerializer(membership).data
                return None
            except Exception:
                return None

    def get_created_at_est(self, obj):
        """Return created_at in EST timezone"""
        if obj.created_at:
            est = pytz.timezone("America/New_York")
            return obj.created_at.astimezone(est).isoformat()
        return None

    def get_draft_started_at_est(self, obj):
        """Return draft_started_at in EST timezone"""
        if obj.draft_started_at:
            est = pytz.timezone("America/New_York")
            return obj.draft_started_at.astimezone(est).isoformat()
        return None

    def get_draft_completed_at_est(self, obj):
        """Return draft_completed_at in EST timezone"""
        if obj.draft_completed_at:
            est = pytz.timezone("America/New_York")
            return obj.draft_completed_at.astimezone(est).isoformat()
        return None
        return None


class LeagueMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    league_name = serializers.CharField(source='league.name', read_only=True)
    joined_at_est = serializers.SerializerMethodField()

    class Meta:
        model = LeagueMembership
        fields = [
            "id",
            "user",
            "league",
            "league_name",
            "team_name",
            "is_admin",
            "joined_at",
            "joined_at_est",
        ]
        read_only_fields = ['id', 'user', 'joined_at']

    def get_joined_at_est(self, obj):
        """Return joined_at in EST timezone"""
        if obj.joined_at:
            est = pytz.timezone("America/New_York")
            return obj.joined_at.astimezone(est).isoformat()
        return None


class DraftedTeamSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    league_name = serializers.CharField(source='league.name', read_only=True)
    drafted_at_est = serializers.SerializerMethodField()

    class Meta:
        model = DraftedTeam
        fields = [
            "id",
            "league",
            "league_name",
            "user",
            "team_name",
            "player_id",
            "player_name",
            "position",
            "team",
            "fantasy_points",
            "drafted_at",
            "drafted_at_est",
            "draft_order",
        ]
        read_only_fields = ['id', 'drafted_at']

    def get_drafted_at_est(self, obj):
        """Return drafted_at in EST timezone"""
        if obj.drafted_at:
            est = pytz.timezone("America/New_York")
            return obj.drafted_at.astimezone(est).isoformat()
        return None


class DraftPlayerSerializer(serializers.Serializer):
    player_id = serializers.CharField(max_length=50)
    user_id = serializers.IntegerField(required=False)
    team_id = serializers.IntegerField(required=False)

    def validate_user_id(self, value):
        if value:
            try:
                User.objects.get(id=value)
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist")
        return value

    def validate(self, data):
        if not data.get("user_id") and not data.get("team_id"):
            raise serializers.ValidationError("Either user_id or team_id is required")
        return data


class AvailablePlayerSerializer(serializers.Serializer):
    player_id = serializers.CharField()
    name = serializers.CharField()
    position = serializers.CharField()
    team = serializers.CharField()
    fantasy_points = serializers.FloatField()
