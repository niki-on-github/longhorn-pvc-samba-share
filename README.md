# Longhorn PVC Samba Share

Make all longhorn PVC accessible with a samba container.

This container is indented to us in conjunction with my [longhorn-volume-manager](https://github.com/niki-on-github/longhorn-volume-manager) container.

## Variables

Required:

- `NAMESPACE`: The namespace where to deploy the samba container
- `SAMBA_PASSWORD`: The samba password. The default user is `smb` and the share name is `samba`
- `SVC_SAMBA_IP`: The SVC IP for the samba server.

Optional:

- `AFFINITY_HOSTNAME`: hostname where to deploy the samba container
- `ADDITIONAL_HOST_VOLUME_PATHS`: Additional host paths to share

## Usage

See `./example`.

## Limitation

- **Single Node**: The container is currently designed to run in a single node cluster. Multi node cluster could lead to pvc access problems.
- **Single Namespace**: We have different namespaces for our PVC but can only start one pod for the samba port. Maybe we could use the cross namespace data source with Kubernetes `v1.26+`, but this require implementation from longhorn side. See also https://kubernetes.io/docs/concepts/storage/persistent-volumes/#cross-namespace-data-sources. Currently i only need to share one namespace so no problem for now.
