{{/*
Expand the name of the chart.
*/}}
{{- define "store.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "store.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "store.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "store.labels" -}}
helm.sh/chart: {{ include "store.chart" . }}
{{ include "store.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
store.platform/id: {{ .Values.store.id | quote }}
store.platform/engine: {{ .Values.store.engine | quote }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "store.selectorLabels" -}}
app.kubernetes.io/name: {{ include "store.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
MySQL selector labels
*/}}
{{- define "store.mysql.selectorLabels" -}}
{{ include "store.selectorLabels" . }}
app.kubernetes.io/component: mysql
{{- end }}

{{/*
WordPress selector labels
*/}}
{{- define "store.wordpress.selectorLabels" -}}
{{ include "store.selectorLabels" . }}
app.kubernetes.io/component: wordpress
{{- end }}

{{/*
Generate database password
*/}}
{{- define "store.database.password" -}}
{{- if .Values.secrets.database.password }}
{{- .Values.secrets.database.password }}
{{- else }}
{{- randAlphaNum 32 }}
{{- end }}
{{- end }}

{{/*
Generate database root password
*/}}
{{- define "store.database.rootPassword" -}}
{{- if .Values.secrets.database.rootPassword }}
{{- .Values.secrets.database.rootPassword }}
{{- else }}
{{- randAlphaNum 32 }}
{{- end }}
{{- end }}

{{/*
Generate admin password
*/}}
{{- define "store.admin.password" -}}
{{- if .Values.secrets.admin.password }}
{{- .Values.secrets.admin.password }}
{{- else }}
{{- randAlphaNum 24 }}
{{- end }}
{{- end }}

{{/*
MySQL service name
*/}}
{{- define "store.mysql.serviceName" -}}
{{- printf "%s-mysql" .Release.Name }}
{{- end }}

{{/*
WordPress service name
*/}}
{{- define "store.wordpress.serviceName" -}}
{{- printf "%s-wordpress" .Release.Name }}
{{- end }}

{{/*
Store URL
*/}}
{{- define "store.url" -}}
{{- if .Values.ingress.tls.enabled }}
{{- printf "https://%s" .Values.store.domain }}
{{- else }}
{{- printf "http://%s" .Values.store.domain }}
{{- end }}
{{- end }}

{{/*
TLS secret name
*/}}
{{- define "store.tls.secretName" -}}
{{- if .Values.ingress.tls.secretName }}
{{- .Values.ingress.tls.secretName }}
{{- else }}
{{- printf "%s-tls" .Release.Name }}
{{- end }}
{{- end }}
