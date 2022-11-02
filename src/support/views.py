# views.py (support)
# !/usr/bin/env python3
# coding=utf-8
# pylint: skip-file

"""
Views for managing user support functions.

Available functions:
- Create support ticket.
- Save changes to support form.
"""

from decimal import getcontext
from datetime import datetime, timedelta
from os.path import join

# from constants.models import *
from constants.utils import create_qt_email_message
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView

from plastics_eol.settings import MANUAL_NAME, DOWNLOADS_DIR
from .forms import SupportForm, SupportAdminForm, SupportTypeForm, PriorityForm
from .models import SupportType, Support, SupportAttachment, Priority

getcontext().prec = 9


class UserManualView(TemplateView):
    """
    View to present and process the 'request more info' form.

    :param request:
    :return:
    """

    # form_class = InformationRequestForm

    def get(self, request, *args, **kwargs):
        """Present the request info form."""
        return render(request, 'main/manual.html', {})


class EventsView(TemplateView):
    """Support Upcoming Events view."""

    def get(self, request, *args, **kwargs):
        """
        :param request:.

        :param args:
        :param kwargs:
        :return:
        """
        return render(request, 'main/events.html', {})


class ReferencesView(TemplateView):
    """Support site References view."""

    def get(self, request, *args, **kwargs):
        """
        :param request:.

        :param args:
        :param kwargs:
        :return:
        """
        return render(request, 'main/references.html', {})


@login_required
def download_manual(request):
    """Download the user manual."""
    return download_file(request, MANUAL_NAME)


def event_file_download(request, *args, **kwargs):
    """Find and download the file matching the provided file name."""
    file_name = kwargs.get('file_name', None)
    return download_file(request, file_name)


def download_file(request, name):
    """Receives the path, name, extension of a file to be returned to user."""
    name_split = name.split('.')
    ext = name_split[len(name_split) - 1]
    file = join(DOWNLOADS_DIR, name)

    if ext == 'docx' or ext == 'pdf' or 'ppt' in ext:
        with open(file, 'rb') as doc:
            response = HttpResponse(doc)
            con_disp = 'attachment; filename="' + name + '"'
            response['Content-Disposition'] = con_disp
            return response

    elif 'xls' in ext:
        with open(file, 'rb') as xls:
            con_type = 'application/vnd.vnd.openxmlformats-officedocument.' + \
                'spreadsheetml.sheet'
            response = HttpResponse(xls, con_type)
            con_disp = 'attachment; filename="' + name + '"'
            response['Content-Disposition'] = con_disp
            return response

    return HttpResponse()


@login_required
def index(request):
    """User login support."""
    user = request.user
    title = 'Support Main Page'

    return render(request, 'main/support.html', locals())


# Start Support


class SuggestionCreateView(FormView):
    """View to create a new support ticket."""

    form_class = SupportForm
    template = 'main/create_support.html'

    @method_decorator(login_required)
    def get(self, request, support_type_name):
        """Display the project create form."""
        if 'suggestion' == support_type_name.lower():
            title = f'Make a suggestion to improve {settings.APP_NAME_LONG}'
            instructions = 'Describe your suggestion for ' + \
                f'{settings.APP_NAME_LONG} below.  You will have the ' + \
                'option to add attachments after saving the suggestion.'
        else:
            title = f'request help with {settings.APP_NAME_LONG}'
            instructions = 'Describe the problem you encountered with ' + \
                f'{settings.APP_NAME_LONG} ' + \
                'below.  You will have the option to add ' + \
                'attachments after saving the request.'
        form = self.form_class(initial={'weblink': request.user.email})
        return render(request, self.template, locals())

    @method_decorator(login_required)
    def post(self, request, support_type_name, *args, **kwargs):
        """Save the changes to the support form."""
        user = request.user
        form = self.form_class(data=request.POST, files=request.FILES)

        if form.is_valid():
            support = form.save(commit=False)
            support.user = user
            support.created_by = user
            support.last_modified_by = user
            # lookup ticket type
            support.support_type = SupportType.objects.filter(
                the_name__iexact=support_type_name).first()
            support.save()

            url = reverse('support:edit_support',
                          kwargs={'support_type_name': support_type_name,
                                  'obj_id': support.id}) + '?new=1'
            return HttpResponseRedirect(url)
        else:
            return render(request, self.template, locals())


class SuggestionEditView(FormView):
    """View to create a new support ticket."""

    form_class = SupportForm
    admin_form_class = SupportAdminForm
    template = 'edit/edit_support.html'
    no_edit_template = 'main/no_edit.html'

    @method_decorator(login_required)
    def get(self, request, support_type_name, obj_id):
        """Handle GET requests from user, return the edit form."""
        user = request.user
        form_class = SupportForm if not user.is_staff else SupportAdminForm
        support = get_object_or_404(Support, id=obj_id)
        support_attachments = SupportAttachment.objects.filter(support=support)

        title = 'Suggestion' if support_type_name == 'suggestion' else 'Help'
        instructions = 'Edit your request or add attachments below.'
        if request.GET.get('new') is not None:
            warn = 'You\'re almost done. Update your suggestion as ' + \
                'needed, add attachments, and then click Submit ' + \
                'to complete your request'

        # make sure the user has permission to edit this support object
        if not user.is_staff and support.user != user:
            return render(request, self.no_edit_template, locals())

        form = form_class(instance=support)
        return render(request, self.template, locals())

    @method_decorator(login_required)
    def post(self, request, support_type_name, obj_id, *args, **kwargs):
        """Save changes to user form."""
        user = request.user
        title = 'Suggestion' if support_type_name == 'suggestion' else 'Help'
        instructions = 'Edit your request or add attachments below.'
        form_class = SupportForm if not user.is_staff else SupportAdminForm
        support = get_object_or_404(Support, id=obj_id)
        support_attachments = SupportAttachment.objects.filter(support=support)

        # make sure the user has permission to edit this support object
        if not user.is_staff and support.user != user:
            return render(request, self.no_edit_template, locals())

        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            support.modified = request.user
            support.subject = form.cleaned_data['subject']
            support.the_description = form.cleaned_data['the_description']
            support.weblink = form.cleaned_data['weblink']
            if user.is_staff:
                support.date_resolved = form.cleaned_data['date_resolved']
                support.review_notes = form.cleaned_data['review_notes']

            support.save()

            # reload the attachment list
            support_attachments = SupportAttachment.objects.filter(
                support=support)

            # email the DataSearch admins and cc the user
            # get type of ticket
            if support.support_type is not None:
                support_type_desc = support.support_type.the_name
            else:
                support_type_desc = support_type_name

            support_email = settings.SUPPORT_EMAIL
            submitter_email = support.weblink
            email_to = support_email
            email_to.append(submitter_email)

            # detect if this is a new request versus editing
            # if it's an update, we add language to the subject and
            # body to indicate that to the recipient.
            referer_url = request.META['HTTP_REFERER']
            if referer_url.endswith('?new=1'):
                email_subject = f'{settings.APP_NAME_LONG} ' + \
                    f'{support_type_desc} {obj_id}: {support.subject}'
                email_body = support.the_description
            else:
                email_subject = \
                    f'UPDATED: {settings.APP_NAME_LONG} support_type_desc' + \
                    f' {obj_id}: {support.subject}'
                email_body = 'This automated email is to notify you ' + \
                    'that your support request has been updated.\r\n\r\n' + \
                    'Description:\r\n' + str(support.the_description) + \
                    '\r\n\r\nDate Resolved: ' + str(support.date_resolved) + \
                    '\r\n\r\nReview Notes:\r\n' + str(support.review_notes)

            the_email = create_qt_email_message(
                email_subject, email_body, support_email, email_to)

            for att in support_attachments:
                the_email.attach_file(
                    settings.MEDIA_ROOT + '/' + str(att.attachment))

            if not settings.EMAIL_DISABLED:
                the_email.send(fail_silently=False)

            # Go to show detail page next.
            if support_type_name == 'suggestion':
                url = '/support/show/%s/' % str(obj_id)
            else:
                url = '/support/show/%s/' % str(obj_id)

            return HttpResponseRedirect(url)

        else:
            return render(request, self.template, locals())


@login_required
@never_cache
def show_support(request, obj_id):
    """Support request view."""
    user = request.user
    obj = get_object_or_404(Support, id=obj_id)
    support = Support.objects.get(id=obj_id)
    title = 'Show Support'
    support_attachments = SupportAttachment.objects.filter(support=obj)
    return render(request, 'show/show_support.html', locals())


@login_required
def file_upload_support(request, obj_id):
    """Ensure user logged into app."""
    user = request.user
    support = Support.objects.get(id=obj_id)

    # if not user.is_staff and support.user != user:
    #     ctx['error_message'] = 'You are not authorized to add files.'
    #     return render(request, '', ctx)

    if user.is_staff or support.user == user:
        for new_file in request.FILES.getlist('upl'):
            # Create a new entry in our database
            support_attachment, created = \
                SupportAttachment.objects.get_or_create(
                    support=support, attachment=new_file,
                    the_name=new_file.name,
                    user=user, the_size=new_file.size)

    support_type_name = 'suggestion' if 'uggest' in \
        support.support_type.the_name else 'help'
    url = reverse('support:edit_support',
                  kwargs={'obj_id': support.id,
                          'support_type_name': support_type_name})
    return HttpResponseRedirect(url)


@login_required
def delete_support(request, support_type_name, obj_id):
    """Delete ticket."""
    user = request.user
    support = get_object_or_404(Support, id=obj_id)

    if user.is_staff:
        support.delete()

    url = reverse('support:list_supports',
                  kwargs={'support_type_name': support_type_name})
    return HttpResponseRedirect(url)


@login_required
def list_supports(request, support_type_name):
    """List tickets."""
    user = request.user
    title = 'Support List'
    # supports = Support.objects.all()
    supports = Support.objects.filter(
        support_type__the_name__iexact=support_type_name)
    return render(request, 'list/list_support_issues.html', locals())


@login_required
def delete_support_attachment(request, obj_id):
    """Delete attachments for support tickets."""
    title = 'Delete Support Attachment'
    user = request.user
    support_attachment = get_object_or_404(SupportAttachment, id=obj_id)
    support = support_attachment.support
    support_id = support.id

    profile = user.userprofile
    obj = get_object_or_404(Support, id=support_id)
    title = 'Support'

    support_attachments = SupportAttachment.objects.filter(support=obj)

    try:
        if support_attachment.user == user or profile.user_type == 'SUPER':
            support_attachment.delete()
        else:
            error = 'You are not authorized to delete this attachment.'
    except Exception:
        error = 'Failed to delete attachment. Please try again.'

    return render(request, 'show/show_support.html', locals())


@login_required
def search_support_for_last_30(request):
    """Search new tickets last 30-days."""
    user = request.user
    query = Q()
    query_show = 'Support Requests Received For Last 30 Days'

    title = 'Support Requests Received Last 30 Days - With Results Shown'
    d = datetime.today() - timedelta(days=30)
    if user.is_staff:
        query = Q(created__gte=d)
    else:
        query = Q(created__gte=d) & Q(user=user)

    if query:
        the_count = Support.objects.filter(query).count()
        objs = Support.objects.filter(query)
    else:
        objs = ''

    return render(request, 'list/list_support_issues.html', locals())


@login_required
def search_support_for_last_60(request):
    """Search new tickets last 60-days.."""
    user = request.user
    query = Q()
    query_show = 'Support Requests Received For Last 60 Days'

    title = 'Support Requests Received Last 60 Days - With Results Shown'
    d = datetime.today() - timedelta(days=60)
    if user.is_staff:
        query = Q(created__gte=d)
    else:
        query = Q(created__gte=d) & Q(user=user)

    if query:
        the_count = Support.objects.filter(query).count()
        objs = Support.objects.filter(query)
    else:
        objs = ''

    return render(request, 'list/list_support_issues.html', locals())


@login_required
def search_support_for_last_90(request):
    """Search new tickets last 90-days."""
    user = request.user
    query = Q()
    query_show = 'Support Requests Received For Last 90 Days'

    title = 'Support Requests Received Last 90 Days - With Results Shown'
    d = datetime.today() - timedelta(days=90)
    if user.is_staff:
        query = Q(created__gte=d)
    else:
        query = Q(created__gte=d) & Q(user=user)

    if query:
        the_count = Support.objects.filter(query).count()
        objs = Support.objects.filter(query)
    else:
        objs = ''

    return render(request, 'list/list_support_issues.html', locals())


@login_required
def search_support_for_last_180(request):
    """Search new tickets last 180-days."""
    user = request.user
    query = Q()
    query_show = 'Support Requests Received For Last 180 Days'

    title = 'Support Requests Received Last 180 Days - With Results Shown'
    d = datetime.today() - timedelta(days=180)
    if user.is_staff:
        query = Q(created__gte=d)
    else:
        query = Q(created__gte=d) & Q(user=user)

    if query:
        the_count = Support.objects.filter(query).count()
        objs = Support.objects.filter(query)
    else:
        objs = ''

    return render(request, 'list/list_support_issues.html', locals())


# End Support

# Start SupportType

@login_required
def create_support_type(request):
    """Ticket support type."""
    user = request.user
    title = 'Create a New SupportType'
    support_types = SupportType.objects.all()

    if request.method == 'POST':
        form = SupportTypeForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            if 'files' in request.FILES:
                files = request.FILES['files']
                files.user = user

            support_type = form.save(commit=False)

            support_type.user = user
            support_type.created_by = user.username
            support_type.last_modified_by = user.username
            support_type.save()

            url = reverse('support:show_support_type',
                          kwargs={'obj_id': support_type.id})
            return HttpResponseRedirect(url)
    else:
        form = SupportTypeForm()
    return render(request, 'create_office.html', locals())


@login_required
def edit_support_type(request, obj_id):
    """Edit support type."""
    user = request.user

    title = 'Update SupportType'

    support_type = SupportType.objects.get(id=obj_id)
    support_types = SupportType.objects.all()

    if user.is_staff or user == support_type.user:
        pass
    else:
        return render(request, 'no_edit.html', locals())

    if support_type.user == user:
        if request.method == 'POST':
            form = SupportTypeForm(data=request.POST, files=request.FILES,
                                   instance=support_type)
            if form.is_valid():
                support_type = form.save(commit=False)

                support_type.last_modified_by = user.username
                support_type.save()

                url = reverse('support:show_support_type',
                              kwargs={'obj_id': support_type.id})
                return HttpResponseRedirect(url)
        else:
            form = SupportTypeForm(instance=support_type)
    else:
        url = '/accounts/not_authorized/'

    return render(request, 'edit_office.html', locals())


@login_required
def delete_support_type(request, obj_id):
    """Remove an available support type from the database."""
    user = request.user
    support_type = get_object_or_404(SupportType, id=obj_id)

    if support_type.user == user:
        support_type.delete()

    url = reverse('support:list_support_types')
    return HttpResponseRedirect(url)


@login_required
def list_support_types(request):
    """Return a view containing the list of available support types."""
    user = request.user
    title = 'SupportType List'
    support_types = SupportType.objects.all().order_by('ordering')
    return render(request, 'list/list_support_types.html', locals())


@login_required
@never_cache
def show_support_type(request, obj_id):
    """Return a view showing details of a selected support type."""
    user = request.user
    obj = get_object_or_404(SupportType, id=obj_id)
    title = 'Show SupportType'
    support_types = SupportType.objects.all().order_by('ordering')
    return render(request, 'show/show.html', locals())


def search_support_type(request):
    """Return a view where the user can search for support types."""
    title = 'Search For SupportType - With Results Shown'
    return render(request, 'main/search_support_type.html', locals())


# End SupportType

# Start Priority

@login_required
def create_priority(request):
    """
    Create a new priority object in the database.

    This method handles both POST (handling user data to create the object),
    and GET (providing user the form to create a new object) requests.
    """
    user = request.user
    title = 'Create a New Priority'
    priorities = Priority.objects.all()

    if request.method == 'POST':
        form = PriorityForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            if 'files' in request.FILES:
                files = request.FILES['files']
                files.user = user

            priority = form.save(commit=False)

            priority.user = user
            priority.created_by = user.username
            priority.last_modified_by = user.username
            priority.save()

            url = reverse('support:show_priority',
                          kwargs={'obj_id': priority.id})
            return HttpResponseRedirect(url)
    else:
        form = PriorityForm()
    return render(request, 'create_office.html', locals())


@login_required
def edit_priority(request, obj_id):
    """
    Edit a priority object.

    GET: Return a view to allow the user to edit a selected priority object.
    POST: Save the user's changes to the selected priority object.
    """
    user = request.user

    title = 'Update Priority'

    priority = Priority.objects.get(id=obj_id)
    priorities = Priority.objects.all()

    if user.is_staff or user == priority.user:
        pass
    else:
        return render(request, 'no_edit.html', locals())

    if priority.user == user:
        if request.method == 'POST':
            form = PriorityForm(data=request.POST, files=request.FILES,
                                instance=priority)
            if form.is_valid():
                priority = form.save(commit=False)

                priority.last_modified_by = user.username
                priority.save()

                url = reverse('support:show_priority',
                              kwargs={'obj_id': priority.id})
                return HttpResponseRedirect(url)
        else:
            form = PriorityForm(instance=priority)
    else:
        url = '/accounts/not_authorized/'

    return render(request, 'edit_office.html', locals())


@login_required
def delete_priority(request, obj_id):
    """Delete priority objects from the database."""
    user = request.user
    priority = get_object_or_404(Priority, id=obj_id)

    if priority.user == user:
        priority.delete()

    url = reverse('support:list_priorities')
    return HttpResponseRedirect(url)


@login_required
def list_priorities(request):
    """Return a view containing a list of available Priority objects."""
    user = request.user
    title = 'Priority List'
    priorities = Priority.objects.all().order_by('ordering')
    return render(request, 'list/list_priorities.html', locals())


@login_required
@never_cache
def show_priority(request, obj_id):
    """Return a view showing the details of a selected priority."""
    user = request.user
    obj = get_object_or_404(Priority, id=obj_id)
    title = 'Show Priority'
    return render(request, 'show/show.html', locals())


def search_priority(request):
    """Return a view where the user can search for Priority objects."""
    title = 'Search For Priority - With Results Shown'
    return render(request, 'main/search_priority.html', locals())


def replace_none_empty_str(data_dict):
    """
    Replace None with an empty string.

    This method will search for values of None in a dictionary
    and replace them with empty strings.
    """
    for key, value in data_dict.items():
        if value is None:
            data_dict[key] = ""
    return data_dict