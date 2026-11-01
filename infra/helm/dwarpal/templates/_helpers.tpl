{{/* Shared pieces for the chart's templates. */}}

{{/* A component's image: registry/owner/name:tag, the tag defaulting to the chart's appVersion. */}}
{{- define "dwarpal.image" -}}
{{- $root := index . 0 -}}{{- $name := index . 1 -}}
{{- printf "%s/%s/%s:%s" $root.Values.image.registry (lower $root.Values.image.owner) $name (default $root.Chart.AppVersion $root.Values.image.tag) -}}
{{- end -}}

{{/* Labels every object carries, so tools can find what belongs to this release. */}}
{{- define "dwarpal.labels" -}}
app.kubernetes.io/name: dwarpal
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}
