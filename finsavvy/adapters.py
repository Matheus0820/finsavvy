from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount import app_settings
from django.db.models import Q

class FinsavvySocialAccountAdapter(DefaultSocialAccountAdapter):
    def list_apps(self, request, provider=None, client_id=None):
        from allauth.socialaccount.models import SocialApp

        provider_to_apps = {}

        # 1. Populate settings apps first
        for p, pcfg in app_settings.PROVIDERS.items():
            if provider and p != provider:
                continue
            app_configs = pcfg.get("APPS")
            if app_configs is None:
                app_config = pcfg.get("APP")
                if app_config is None:
                    continue
                app_configs = [app_config]

            apps = provider_to_apps.setdefault(p, [])
            for config in app_configs:
                app = SocialApp(provider=p)
                for field in ["name", "provider_id", "client_id", "secret", "key", "settings"]:
                    if field in config:
                        setattr(app, field, config[field])
                if client_id and app.client_id != client_id:
                    continue
                apps.append(app)

        # 2. Fallback / blend with DB apps (settings take precedence)
        if request:
            db_apps = SocialApp.objects.on_site(request)
        else:
            db_apps = SocialApp.objects.all()
        if provider:
            db_apps = db_apps.filter(Q(provider=provider) | Q(provider_id=provider))
        if client_id:
            db_apps = db_apps.filter(client_id=client_id)

        for app in db_apps:
            if app.provider in provider_to_apps and provider_to_apps[app.provider]:
                continue
            apps = provider_to_apps.setdefault(app.provider, [])
            apps.append(app)

        all_apps = []
        for provider_apps in provider_to_apps.values():
            all_apps.extend(provider_apps)
        return all_apps
