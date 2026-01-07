from rest_framework import serializers
from django.contrib.auth.models import User
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
    
    class Meta:
        model = League
        fields = [
            'id', 'name', 'created_by', 'created_at', 'num_teams',
            'positions_included', 'scoring_settings', 'is_draft_complete',
            'draft_started_at', 'draft_completed_at', 'member_count',
            'user_membership'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'draft_started_at', 'draft_completed_at']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_user_membership(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                membership = LeagueMembership.objects.get(user=request.user, league=obj)
                return LeagueMembershipSerializer(membership).data
            except LeagueMembership.DoesNotExist:
                return None
        return None


class LeagueMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    league_name = serializers.CharField(source='league.name', read_only=True)
    
    class Meta:
        model = LeagueMembership
        fields = ['id', 'user', 'league', 'league_name', 'team_name', 'is_admin', 'joined_at']
        read_only_fields = ['id', 'user', 'joined_at']


class DraftedTeamSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    league_name = serializers.CharField(source='league.name', read_only=True)
    
    class Meta:
        model = DraftedTeam
        fields = [
            'id', 'league', 'league_name', 'user', 'team_name', 'player_id',
            'player_name', 'position', 'team', 'fantasy_points',
            'drafted_at', 'draft_order'
        ]
        read_only_fields = ['id', 'drafted_at']


class DraftPlayerSerializer(serializers.Serializer):
    player_id = serializers.CharField(max_length=50)
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")


class AvailablePlayerSerializer(serializers.Serializer):
    player_id = serializers.CharField()
    name = serializers.CharField()
    position = serializers.CharField()
    team = serializers.CharField()
    fantasy_points = serializers.FloatField()