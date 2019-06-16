from django.http import JsonResponse
from django.views import generic

from tests.testapp import forms


class ExampleFormView(generic.FormView):
    form_class = forms.UploadForm
    template_name = 'form.html'

    def form_valid(self, form):
        return JsonResponse(self.request.POST, status=201)
