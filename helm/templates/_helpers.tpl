{{- define "openmeals.name" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "openmeals.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "openmeals.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "openmeals.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "openmeals.selectorLabels" -}}
app.kubernetes.io/name: {{ include "openmeals.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "openmeals.apiImage" -}}
{{ .Values.image.registry }}/{{ .Values.image.repository }}/api:{{ .Values.image.tag }}
{{- end }}

{{- define "openmeals.workerImage" -}}
{{ .Values.image.registry }}/{{ .Values.image.repository }}/worker:{{ .Values.image.tag }}
{{- end }}
