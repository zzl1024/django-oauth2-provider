# Create your views here.
from datetime import datetime, timedelta
from django.core.urlresolvers import reverse
from provider.oauth2.auth import BasicClientBackend, RequestParamsClientBackend
from provider.oauth2.forms import AuthorizationRequestForm, AuthorizationForm, \
    GrantForm, RefreshTokenForm
from provider.oauth2.models import Client, RefreshToken, AccessToken
from provider.views import Capture, Authorize, Redirect, \
    AccessToken as AccessTokenView

class Mixin(object):
    pass

class Capture(Capture, Mixin):
    def get_redirect_url(self, request):
        return reverse('oauth2:authorize-2')
    
class Authorize(Authorize, Mixin):
    def get_request_form(self, client, data):
        return AuthorizationRequestForm(data, client=client)
    
    def get_authorization_form(self, request, client, data, client_data):
        return AuthorizationForm(data)
    
    def get_client(self, client_id):
        try:
            return Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            return None

    def get_redirect_url(self, request):
        return reverse('oauth2:redirect')

    def save_authorization(self, request, client, form, client_data):
        grant = form.save(commit=False)

        if grant is None:
            return None

        grant.user = request.user
        grant.client = client
        grant.redirect_uri = client_data.get('redirect_uri', '')
        grant.scope = client_data.get('scope', '')
        grant.save()
        return grant.code


class Redirect(Redirect, Mixin):
    pass

class AccessTokenView(AccessTokenView, Mixin):
    authentication = (
        BasicClientBackend,
        RequestParamsClientBackend,
    )
    
    def get_grant(self, request, data, client):
        form = GrantForm(data, client=client)
        if form.is_valid():
            return True, form.cleaned_data.get('grant')
        return False, form.errors

    def get_refresh_token(self, request, data, client):
        form = RefreshTokenForm(data, client=client)
        if form.is_valid():
            return True, form.cleaned_data.get('refresh_token')
        return False, form.errors
        
    def create_access_token(self, request, user, scope, client):
        return AccessToken.objects.create(
            user=user,
            client=client,
            scope=scope
        )
            
    def create_refresh_token(self, request, user, scope, access_token, client):
        return RefreshToken.objects.create(
            user=user,
            access_token=access_token,
            client=client
        )
    
    def invalidate_grant(self, grant):
        grant.expires = datetime.now() - timedelta(days=1)
        grant.save()
        
    def invalidate_refresh_token(self, rt):
        rt.expired = True
        rt.save()
        
    
    def invalidate_access_token(self, at):
        at.expires = datetime.now() - timedelta(days=1)
        at.save()
