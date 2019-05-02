from __future__ import absolute_import

from rest_framework.response import Response

from sentry import features
from sentry.api.base import Endpoint
from sentry.api.bases.incident import IncidentPermission
from sentry.api.exceptions import ResourceDoesNotExist
from sentry.api.serializers import serialize
from sentry.incidents.models import Incident
from sentry.utils.sdk import configure_scope


class IncidentDetailsEndpoint(Endpoint):
    permission_classes = (IncidentPermission, )

    def convert_args(self, request, incident_id, *args, **kwargs):
        try:
            incident = Incident.objects.select_related('organization').get(id=incident_id)
        except Incident.DoesNotExist:
            raise ResourceDoesNotExist

        self.check_object_permissions(request, incident.organization)

        with configure_scope() as scope:
            scope.set_tag("organization", incident.organization_id)

        request._request.organization = incident.organization

        kwargs['incident'] = incident
        return args, kwargs

    def get(self, request, incident):
        """
        Fetch an Incident.
        ``````````````````
        :auth: required
        """
        if not features.has('organizations:incidents', incident.organization, actor=request.user):
            return self.respond(status=404)

        return Response(serialize(incident, request.user))
