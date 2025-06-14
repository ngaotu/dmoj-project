# coding=utf-8
import re

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import get_default_password_validators
from django.forms import ChoiceField, ModelChoiceField
from django.shortcuts import render
from django.utils.translation import gettext as _, gettext_lazy, ngettext
from django.db import transaction

from registration.backends.default.views import (ActivationView as OldActivationView,
                                                 RegistrationView as OldRegistrationView)
from registration.forms import RegistrationForm
from sortedm2m.forms import SortedMultipleChoiceField

from judge.models import Language, Organization, Profile, TIMEZONE
from judge.utils.recaptcha import ReCaptchaField, ReCaptchaWidget
from judge.utils.subscription import Subscription, newsletter_id
from judge.widgets import Select2MultipleWidget, Select2Widget


bad_mail_regex = list(map(re.compile, settings.BAD_MAIL_PROVIDER_REGEX))


class CustomRegistrationForm(RegistrationForm):
    username = forms.RegexField(regex=r'^\w+$', max_length=30, label=gettext_lazy('Username'),
                                error_messages={'invalid': gettext_lazy('A username must contain letters, '
                                                             'numbers, or underscores.')})
    full_name = forms.CharField(max_length=30, label=gettext_lazy('Full name'), required=False)
    timezone = ChoiceField(label=gettext_lazy('Timezone'), choices=TIMEZONE,
                           widget=Select2Widget(attrs={'style': 'width:100%'}))
    language = ModelChoiceField(queryset=Language.objects.all(), label=gettext_lazy('Preferred language'), empty_label=None,
                                widget=Select2Widget(attrs={'style': 'width:100%'}))
    organizations = SortedMultipleChoiceField(queryset=Organization.objects.filter(is_open=True),
                                              label=gettext_lazy('Organizations'), required=False,
                                              widget=Select2MultipleWidget(attrs={'style': 'width:100%'}))

    if newsletter_id is not None:
        newsletter = forms.BooleanField(label=gettext_lazy('Subscribe to newsletter?'), initial=True, required=False)

    if ReCaptchaField is not None:
        captcha = ReCaptchaField(widget=ReCaptchaWidget())

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError(_('The email address "%s" is already taken. Only one registration '
                                                'is allowed per address.') % self.cleaned_data['email'])
        if '@' in self.cleaned_data['email']:
            domain = self.cleaned_data['email'].split('@')[-1].lower()
            if (domain in settings.BAD_MAIL_PROVIDERS or
                    any(regex.match(domain) for regex in bad_mail_regex)):
                raise forms.ValidationError(_('Your email provider is not allowed due to history of abuse. '
                                                    'Please use a reputable email provider.'))
        return self.cleaned_data['email']

    def clean_organizations(self):
        organizations = self.cleaned_data.get('organizations') or []
        max_orgs = settings.DMOJ_USER_MAX_ORGANIZATION_COUNT
        if len(organizations) > max_orgs:
            raise forms.ValidationError(ngettext('You may not be part of more than {count} public organization.',
                                                 'You may not be part of more than {count} public organizations.',
                                                 max_orgs).format(count=max_orgs))
        return self.cleaned_data['organizations']


class RegistrationView(OldRegistrationView):
    title = _('')
    form_class = CustomRegistrationForm
    template_name = 'registration/registration_form.html'

    def get_context_data(self, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = self.title
        kwargs['TIMEZONE_MAP'] = settings.TIMEZONE_MAP
        kwargs['password_validators'] = get_default_password_validators()
        kwargs['tos_url'] = settings.TERMS_OF_SERVICE_URL
        return super(RegistrationView, self).get_context_data(**kwargs)

    def register(self, form):
        user = super(RegistrationView, self).register(form)
        profile, _ = Profile.objects.get_or_create(user=user, defaults={
            'language': Language.get_default_language(),
        })

        cleaned_data = form.cleaned_data
        user.first_name = cleaned_data['full_name']
        profile.timezone = cleaned_data['timezone']
        profile.language = cleaned_data['language']
        profile.organizations.add(*cleaned_data['organizations'])
        with transaction.atomic():
            user.save()
            profile.save()
        # profile.save()

        if newsletter_id is not None and cleaned_data['newsletter']:
            Subscription(user=user, newsletter_id=newsletter_id, subscribed=True).save()
        return user

    def get_initial(self, *args, **kwargs):
        initial = super(RegistrationView, self).get_initial(*args, **kwargs)
        initial['timezone'] = settings.DEFAULT_USER_TIME_ZONE
        initial['language'] = Language.objects.get(key=settings.DEFAULT_USER_LANGUAGE)
        return initial


class ActivationView(OldActivationView):
    title = _('Activation Key Invalid')
    template_name = 'registration/activate.html'

    def get_context_data(self, **kwargs):
        if 'title' not in kwargs:
            kwargs['title'] = self.title
        return super(ActivationView, self).get_context_data(**kwargs)


def social_auth_error(request):
    return render(request, 'generic-message.html', {
        'title': gettext('Authentication failure'),
        'message': request.GET.get('message'),
    })
